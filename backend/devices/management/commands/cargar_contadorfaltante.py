import csv
import ipaddress
import os

from django.core.management.base import BaseCommand
from django.db.models import Q

from devices.models import Impresora, MonthlyCounterEntry


def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def to_int(value):
    value = (value or "").strip()
    if not value:
        return None
    value = value.replace(".", "").replace(",", "")
    return int(value)


class Command(BaseCommand):
    help = "Carga MonthlyCounterEntry faltantes desde contadorfaltante.txt"

    def add_arguments(self, parser):
        default_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir, "contadorfaltante.txt"
            )
        )
        parser.add_argument(
            "--path",
            type=str,
            default=default_path,
            help="Ruta al archivo contadorfaltante.txt",
        )
        parser.add_argument(
            "--period",
            type=str,
            default="jul-26",
            help="Periodo a asignar a los nuevos registros",
        )

    def handle(self, *args, **options):
        path = options["path"]
        period = options["period"]

        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"No existe {path}"))
            return

        created = 0
        skipped = 0
        malformed = 0

        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if not row or not any(x.strip() for x in row):
                    continue

                if len(row) < 5:
                    malformed += 1
                    continue

                name = row[0].strip()
                model = row[1].strip()
                third = row[2].strip()
                fourth = row[3].strip()

                # Determinar cuál es la IP y cuál el serial
                if is_ip(third) and not is_ip(fourth):
                    ip, serial = third, fourth
                elif is_ip(fourth) and not is_ip(third):
                    ip, serial = fourth, third
                elif third and not fourth:
                    ip, serial = "", third
                elif fourth and not third:
                    ip, serial = "", fourth
                elif third.count(".") >= 3 and fourth.count(".") < 3:
                    ip, serial = third, fourth
                elif fourth.count(".") >= 3 and third.count(".") < 3:
                    ip, serial = fourth, third
                else:
                    malformed += 1
                    continue

                # Buscar Impresora
                q = Q()
                if ip:
                    q |= Q(ip_address=ip)
                if serial:
                    q |= Q(serial_number=serial)

                impresora = Impresora.objects.filter(q).first()

                # Preparar valores
                data = {
                    "display_name": model,
                    "ip_address": ip,
                    "serial_number": serial,
                    "period": period,
                    "source_file": os.path.basename(path),
                }

                # Mapear contadores
                if len(row) > 4:
                    data["previous_month_counter"] = to_int(row[4])
                if len(row) > 5:
                    data["week1_counter"] = to_int(row[5])
                if len(row) > 6:
                    data["week1_final"] = to_int(row[6])
                if len(row) > 7:
                    data["week2_counter"] = to_int(row[7])
                if len(row) > 8:
                    data["week2_final"] = to_int(row[8])
                if len(row) > 9:
                    data["week3_counter"] = to_int(row[9])
                if len(row) > 10:
                    data["week3_final"] = to_int(row[10])
                if len(row) > 11:
                    data["week4_counter"] = to_int(row[11])
                if len(row) > 12:
                    data["week4_final"] = to_int(row[12])
                if len(row) > 13:
                    data["week5_counter"] = to_int(row[13])
                if len(row) > 14:
                    data["week5_final"] = to_int(row[14])
                if len(row) > 15:
                    data["monthly_counter"] = to_int(row[15])

                # Si hay Impresora, vincular y copiar status
                if impresora:
                    data["impresora"] = impresora
                    data["printer_status"] = impresora.status
                else:
                    data["printer_status"] = "Instalado"

                # Evitar duplicados por IP/serial + periodo
                filters = {"period": period}
                if ip:
                    filters["ip_address"] = ip
                if serial:
                    filters["serial_number"] = serial

                if not filters.get("ip_address") and not filters.get("serial_number"):
                    malformed += 1
                    continue

                entry, is_new = MonthlyCounterEntry.objects.update_or_create(
                    defaults=data, **filters
                )

                if is_new:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Creados: {created}; actualizados/existentes: {skipped}; mal formados: {malformed}"
            )
        )
