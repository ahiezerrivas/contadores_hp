"""
Detecta automaticamente en que semana del mes estamos (bloques lunes-viernes,
contados desde el primer lunes del mes) y actualiza MonthlyCounterEntry para
esa semana usando los DeviceSnapshot mas recientes.

Pensado para correrse despues de cada run_export (se invoca automaticamente
al final de run_export), asi los contadores quedan al dia sin depender de
que alguien corra actualizar_contadores_semana manualmente cada semana.

Si la fecha de referencia cae antes del primer lunes del mes (dias sueltos
que no pertenecen a ninguna semana segun la regla de negocio), no hace nada.

Uso:
    python manage.py actualizar_semana_actual
    python manage.py actualizar_semana_actual --date 2026-07-29
    python manage.py actualizar_semana_actual --dry-run
"""

import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from devices.utils import get_week_bounds


class Command(BaseCommand):
    help = "Detecta la semana actual (lunes-viernes) y corre actualizar_contadores_semana."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=None,
            help="Fecha de referencia (YYYY-MM-DD). Por defecto: hoy.",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--status",
            default=None,
            help="Filtrar solo impresoras con este status (ej: Instalado).",
        )

    def handle(self, *args, **options):
        date_arg = options.get("date")
        if date_arg:
            try:
                today = datetime.date.fromisoformat(date_arg)
            except ValueError as exc:
                raise CommandError(f"Fecha invalida: {exc}")
        else:
            today = timezone.localtime().date()

        info = get_week_bounds(today)
        if not info:
            self.stdout.write(
                self.style.WARNING(
                    f"{today} no pertenece a ninguna semana (antes del primer lunes "
                    "del mes, fin de semana fuera de rango, o mas alla de la semana 5). "
                    "No se actualizo nada."
                )
            )
            return

        period, week_number, week_start, week_end = info
        effective_end = min(week_end, today)

        self.stdout.write(
            f"Detectado: periodo={period} semana={week_number} "
            f"rango={week_start}..{effective_end}"
        )

        call_command(
            "actualizar_contadores_semana",
            period=period,
            week=week_number,
            start=str(week_start),
            end=str(effective_end),
            dry_run=options.get("dry_run", False),
            status=options.get("status"),
        )
