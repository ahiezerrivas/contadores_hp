"""
Carga oficinas e impresoras desde un archivo TSV hacia MonthlyCounterEntry.

Columnas esperadas (tab separadas):
    Region <tab> Nombre Oficina <tab> Codigo de Oficina <tab> Nombre de Host Oficina <tab> DisplayName <tab> Serial <tab> IPv4Address

Uso:
    python manage.py import_oficinas_e_impresoras "backend/devices/oficinas e impresoras.txt"
    python manage.py import_oficinas_e_impresoras "backend/devices/oficinas e impresoras.txt" --flush
"""

from django.core.management.base import BaseCommand, CommandError

from devices.models import MonthlyCounterEntry, Oficina


class Command(BaseCommand):
    help = (
        "Carga oficinas e impresoras desde un archivo TSV hacia MonthlyCounterEntry."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help=(
                "Ruta al archivo .txt con columnas: Region <tab> Nombre Oficina "
                "<tab> Codigo de Oficina <tab> Nombre de Host Oficina <tab> "
                "DisplayName <tab> Serial <tab> IPv4Address"
            ),
        )
        parser.add_argument(
            "--encoding",
            default="utf-8",
            help="Codificacion del archivo (por defecto utf-8).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina los registros de MonthlyCounterEntry que provengan de este archivo antes de importar.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        encoding = options["encoding"]
        flush = options["flush"]

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

        if flush:
            deleted, _ = MonthlyCounterEntry.objects.filter(source_file=path).delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Se eliminaron {deleted} registros anteriores importados desde este archivo."
                )
            )

        created = 0
        updated = 0
        skipped = 0

        for raw in lines[start:]:
            line = raw.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split("\t")]
            if len(parts) < 7:
                parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                skipped += 1
                continue

            (
                region,
                office_name,
                code,
                host_name,
                display_name,
                serial,
                ip_address,
            ) = parts[:7]

            if not (serial or ip_address or display_name or host_name):
                skipped += 1
                continue

            if office_name:
                office = Oficina.objects.filter(name=office_name).first()
                if office is None:
                    office = Oficina.objects.create(
                        name=office_name,
                        region=region,
                        code=code,
                        status="Activo",
                    )
                else:
                    office.region = region
                    office.code = code
                    office.save()
            else:
                office = None

            defaults = {
                "region": region,
                "office": office,
                "display_name": display_name,
                "ip_address": ip_address,
                "source_file": path,
            }

            if serial:
                obj, was_created = MonthlyCounterEntry.objects.update_or_create(
                    serial_number=serial,
                    defaults=defaults,
                )
            elif ip_address:
                obj, was_created = MonthlyCounterEntry.objects.update_or_create(
                    ip_address=ip_address,
                    defaults=defaults,
                )
            else:
                skipped += 1
                continue

            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completado: {created} creados, {updated} actualizados, {skipped} omitidos."
            )
        )
