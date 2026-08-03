"""
Conecta a la base de datos SQL Server de HP Web Jetadmin (instancia HPWJA),
descarga informacion de dispositivos y la guarda en Postgres como un nuevo
ExportRun con sus DeviceSnapshot asociados.

Uso:
    python manage.py run_export

Pensado para ser invocado periodicamente (ej. Windows Task Scheduler).
"""

import pyodbc
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from devices.models import DeviceSnapshot, ExportRun, ExportSchedule

QUERY = """
    SELECT
        model_name,
        display_name,
        ipv4_address,
        page_count,
        device_status_severity,
        serial_number,
        system_location
    FROM dbo.PUBLIC_DEV_CON_INFO_VW
    ORDER BY model_name
"""


class Command(BaseCommand):
    help = "Exporta dispositivos desde HP Web Jetadmin (SQL Server) a Postgres."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ejecutar el export aunque no sea la hora programada.",
        )

    def build_conn_str(self):
        return (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={settings.HPWJA_SERVER};"
            f"DATABASE={settings.HPWJA_DATABASE};"
            "Trusted_Connection=yes;"
        )

    def handle(self, *args, **options):
        if not options.get("force") and not ExportSchedule.should_run():
            schedule = ExportSchedule.get_solo()
            now = timezone.localtime()
            self.stdout.write(
                self.style.WARNING(
                    f"Export no ejecutado. "
                    f"enabled={schedule.enabled}, "
                    f"run_time={schedule.run_time}, "
                    f"ahora={now.time()}."
                )
            )
            return

        captured_at = timezone.now()

        try:
            conn = pyodbc.connect(self.build_conn_str(), timeout=10)
        except pyodbc.Error as e:
            ExportRun.objects.create(
                executed_at=captured_at,
                total_devices=0,
                success=False,
                error_message=str(e),
            )
            self.stderr.write(self.style.ERROR(f"Error al conectar a la base de datos: {e}"))
            return

        try:
            cur = conn.cursor()
            cur.execute(QUERY)
            rows = cur.fetchall()
        except pyodbc.Error as e:
            conn.close()
            ExportRun.objects.create(
                executed_at=captured_at,
                total_devices=0,
                success=False,
                error_message=str(e),
            )
            self.stderr.write(self.style.ERROR(f"Error al ejecutar la consulta: {e}"))
            return
        finally:
            conn.close()

        run = ExportRun.objects.create(total_devices=len(rows), success=True)

        snapshots = [
            DeviceSnapshot(
                run=run,
                model_name=(row.model_name or "").strip(),
                display_name=(row.display_name or "").strip(),
                ip_address=(row.ipv4_address or "").strip(),
                page_count=row.page_count,
                device_status_severity=(
                    "" if row.device_status_severity is None else str(row.device_status_severity)
                ),
                serial_number=(row.serial_number or "").strip(),
                system_location=(row.system_location or "").strip(),
                captured_at=run.executed_at,
            )
            for row in rows
        ]
        DeviceSnapshot.objects.bulk_create(snapshots, batch_size=500)

        self.stdout.write(
            self.style.SUCCESS(f"Run #{run.id}: {len(rows)} dispositivos guardados.")
        )

        try:
            call_command("actualizar_semana_actual")
        except Exception as e:
            self.stderr.write(
                self.style.WARNING(
                    f"No se pudo actualizar la semana actual automaticamente: {e}"
                )
            )
