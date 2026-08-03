"""
Carga el catalogo de oficinas desde un archivo TSV
(region <tab> nombre <tab> codigo <tab> status) hacia el modelo Oficina.

Uso:
    python manage.py import_oficinas backend/devices/oficinas.txt --flush
    python manage.py import_oficinas archivo.txt --encoding utf-8
"""

from django.core.management.base import BaseCommand, CommandError

from devices.models import Oficina


class Command(BaseCommand):
    help = "Carga oficinas desde un archivo .txt (tab separado) hacia la tabla Oficina."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al archivo .txt con columnas: Region <tab> Nombre <tab> Codigo <tab> Estatus")
        parser.add_argument(
            "--encoding",
            default="utf-8",
            help="Codificacion del archivo (por defecto utf-8).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina todos los registros existentes en Oficina antes de importar.",
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

        if flush:
            Oficina.objects.all().delete()
            self.stdout.write(self.style.WARNING("Registros anteriores de Oficina eliminados."))

        created = 0
        updated = 0
        skipped = 0

        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split("\t")]
            if len(parts) < 4:
                parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4:
                skipped += 1
                continue

            region, name, code, status_text = parts[0], parts[1], parts[2], parts[3]
            if not name:
                skipped += 1
                continue

            if "Activa" in status_text or "Activo" in status_text:
                status = "Activo"
            else:
                status = "Inactivo"

            _, was_created = Oficina.objects.update_or_create(
                name=name,
                defaults={
                    "region": region,
                    "code": code,
                    "status": status,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completado: {created} creadas, {updated} actualizadas, {skipped} lineas omitidas."
            )
        )
