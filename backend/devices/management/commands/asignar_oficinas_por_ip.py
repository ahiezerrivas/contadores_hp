"""
Asigna la oficina correspondiente a los registros de MonthlyCounterEntry
usando el archivo TSV de oficinas e impresoras como fuente de IPs.

Columnas esperadas (tab separadas):
    Region <tab> Nombre Oficina <tab> Codigo de Oficina <tab> Nombre de Host Oficina <tab> DisplayName <tab> Serial <tab> IPv4Address

Uso:
    python manage.py asignar_oficinas_por_ip "backend/devices/oficinas e impresoras.txt"
"""

from django.core.management.base import BaseCommand, CommandError

from devices.models import MonthlyCounterEntry, Oficina


class Command(BaseCommand):
    help = "Asigna oficinas a MonthlyCounterEntry basandose en IPs de oficinas e impresoras."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help=(
                "Ruta al archivo TSV con columnas: Region <tab> Nombre Oficina "
                "<tab> Codigo de Oficina <tab> Nombre de Host Oficina <tab> "
                "DisplayName <tab> Serial <tab> IPv4Address"
            ),
        )
        parser.add_argument(
            "--encoding",
            default="utf-8",
            help="Codificacion del archivo (por defecto utf-8).",
        )

    def handle(self, *args, **options):
        path = options["path"]
        encoding = options["encoding"]

        try:
            with open(path, encoding=encoding) as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise CommandError(f"No se encontro el archivo: {path}")
        except Exception as exc:
            raise CommandError(f"No se pudo abrir el archivo: {exc}")

        start = 0
        if lines:
            first = lines[0].strip()
            if first and first.split("\t")[0].strip().lower() == "region":
                start = 1

        # Cargar mapeo IP -> Oficina y datos auxiliares
        ip_to_office = {}
        ip_to_region = {}
        seen_ips = set()

        for raw in lines[start:]:
            line = raw.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split("\t")]
            if len(parts) < 7:
                parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                continue

            region, office_name, code, _, display_name, serial, ip = (
                parts[:7]
            )
            if not (office_name and ip):
                continue

            # La ultima aparicion de la IP gana (por si hay duplicados)
            ip_to_office[ip] = office_name
            ip_to_region[ip] = region

        matched = 0
        not_found = 0

        for ip, office_name in ip_to_office.items():
            office = Oficina.objects.filter(name=office_name).first()
            if office is None:
                office = Oficina.objects.create(
                    name=office_name,
                    region=ip_to_region[ip],
                    code="",
                    status="Activo",
                )

            updated = MonthlyCounterEntry.objects.filter(ip_address=ip).update(
                office=office
            )

            if updated:
                matched += updated
            else:
                not_found += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Asignacion completada: {matched} registros actualizados, "
                f"{not_found} IPs del archivo sin coincidencia en MonthlyCounterEntry."
            )
        )
