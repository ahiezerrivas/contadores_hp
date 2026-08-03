"""
Compara una lista de IPs (una por linea, en un .txt) contra los dispositivos
que existen actualmente en HP Web Jetadmin (ultimo ExportRun exitoso) y
muestra cuales IPs de la lista NO estan en el sistema.

Uso:
    python manage.py compare_ips "agencia ytore.txt"
    python manage.py compare_ips "agencia ytore.txt" --run 12
    python manage.py compare_ips "agencia ytore.txt" --output faltantes.txt
"""

import re

from django.core.management.base import BaseCommand, CommandError

from devices.models import DeviceSnapshot, ExportRun

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


class Command(BaseCommand):
    help = "Compara una lista de IPs (.txt) contra los dispositivos del ultimo export de HP Web Jetadmin."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al archivo .txt con una IP por linea.")
        parser.add_argument(
            "--run",
            type=int,
            default=None,
            help="ID del ExportRun a usar en vez del ultimo exitoso.",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Si se especifica, escribe las IPs faltantes en este archivo (una por linea).",
        )

    def handle(self, *args, **options):
        path = options["path"]
        try:
            with open(path, "r", encoding="utf-8-sig") as fh:
                lines = [line.strip() for line in fh]
        except FileNotFoundError:
            raise CommandError(f"No se encontro el archivo: {path}")

        file_ips = []
        seen = set()
        skipped = []
        for line in lines:
            if not line:
                continue
            if not IP_RE.match(line):
                skipped.append(line)
                continue
            if line not in seen:
                seen.add(line)
                file_ips.append(line)

        if not file_ips:
            raise CommandError("No se encontraron IPs validas en el archivo.")

        if options["run"]:
            run = ExportRun.objects.filter(id=options["run"]).first()
            if not run:
                raise CommandError(f"No existe un ExportRun con id={options['run']}")
        else:
            run = ExportRun.objects.filter(success=True).order_by("-executed_at").first()
            if not run:
                raise CommandError("No hay ningun ExportRun exitoso registrado todavia.")

        system_ips = set(
            DeviceSnapshot.objects.filter(run=run)
            .exclude(ip_address="")
            .values_list("ip_address", flat=True)
        )

        missing = [ip for ip in file_ips if ip not in system_ips]
        present = [ip for ip in file_ips if ip in system_ips]

        self.stdout.write(
            self.style.NOTICE(
                f"Run usado: #{run.id} ({run.executed_at:%Y-%m-%d %H:%M}) - "
                f"{len(system_ips)} IPs distintas en el sistema."
            )
        )
        self.stdout.write(f"IPs en el archivo: {len(file_ips)}")
        if skipped:
            self.stdout.write(
                self.style.WARNING(f"Lineas ignoradas (no parecen IP): {len(skipped)}")
            )
        self.stdout.write(f"Presentes en el sistema: {len(present)}")
        self.stdout.write(self.style.WARNING(f"Faltantes en el sistema: {len(missing)}"))

        if missing:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("IPs que faltan:"))
            for ip in missing:
                self.stdout.write(f"  {ip}")

        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as fh:
                fh.write("\n".join(missing))
            self.stdout.write(
                self.style.SUCCESS(f"\nIPs faltantes escritas en: {options['output']}")
            )
