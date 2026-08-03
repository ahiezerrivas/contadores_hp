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


class Command(BaseCommand):
    help = "Corrige Impresoras y sus entradas mensuales desde torres.txt"

    def add_arguments(self, parser):
        default_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir, "torres.txt"
            )
        )
        parser.add_argument(
            "--path",
            type=str,
            default=default_path,
            help="Ruta al archivo de texto con los datos corregidos",
        )
        parser.add_argument(
            "--crear-faltantes",
            action="store_true",
            help="Crea Impresora para las filas no encontradas en la base de datos",
        )

    def handle(self, *args, **options):
        path = options["path"]
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"No existe {path}"))
            return

        updated = 0
        not_found = 0
        malformed = 0
        not_found_names = []

        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if not row:
                    continue
                if len(row) != 5:
                    malformed += 1
                    continue

                name, model, third, fourth, status = (x.strip() for x in row)
                if not name or not (third or fourth):
                    malformed += 1
                    continue

                third_is_ip = is_ip(third)
                fourth_is_ip = is_ip(fourth)

                if third_is_ip and not fourth_is_ip:
                    ip, serial = third, fourth
                elif fourth_is_ip and not third_is_ip:
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

                q = Q()
                if ip:
                    q |= Q(ip_address=ip)
                if serial:
                    q |= Q(serial_number=serial)

                impresoras = Impresora.objects.filter(q)
                if not impresoras.exists():
                    if options["crear_faltantes"]:
                        Impresora.objects.create(
                            name=name,
                            model_name=model,
                            ip_address=ip,
                            serial_number=serial,
                            status=status,
                        )
                        updated += 1
                    else:
                        not_found += 1
                        not_found_names.append(f"{name} (ip={ip}, serial={serial})")
                    continue

                impresora_ids = list(impresoras.values_list("id", flat=True))

                Impresora.objects.filter(id__in=impresora_ids).update(
                    name=name,
                    model_name=model,
                    ip_address=ip,
                    serial_number=serial,
                    status=status,
                )

                MonthlyCounterEntry.objects.filter(impresora_id__in=impresora_ids).update(
                    display_name=model,
                    ip_address=ip,
                    serial_number=serial,
                    printer_status=status,
                )

                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Actualizadas: {updated}; no encontradas: {not_found}; mal formadas: {malformed}"
            )
        )

        if not_found_names:
            self.stdout.write("No encontrados:")
            for item in not_found_names[:20]:
                self.stdout.write(f"  - {item}")
            if not_found > 20:
                self.stdout.write(f"  ... y {not_found - 20} mas.")
