"""
Llena week{N}_counter y week{N}_final en MonthlyCounterEntry usando los
DeviceSnapshot capturados durante el rango de fechas de esa semana.

Logica:
  - week{N}_counter = page_count del DeviceSnapshot mas reciente de la IP de la
    impresora, dentro del rango [--start, --end].
  - week{N}_final = week{N}_counter - contador_semana_anterior
      (week{N-1}_counter, o previous_month_counter si N == 1)
  - monthly_counter = suma de todos los week{i}_final no nulos (1..5) de la fila.

  HP Web Jetadmin trunca el digito del millon en el contador (page_count llega
  como si el contador real fuera mod 1.000.000). Si el contador anterior ya
  supera 1.000.000 y el nuevo valor reportado es menor (dando una diferencia
  negativa), se suman millones al valor reportado hasta que quede >= al
  contador anterior, siempre que el resultado de una diferencia semanal
  razonable (< MILLION_ROLLOVER_SANITY_LIMIT). Estas correcciones se listan
  aparte para que se puedan revisar.

Uso:
    python manage.py actualizar_contadores_semana --period jul-26 --week 4 \
        --start 2026-07-27 --end 2026-07-31 --dry-run

    python manage.py actualizar_contadores_semana --period jul-26 --week 4 \
        --start 2026-07-27 --end 2026-07-31
"""

import datetime

from django.core.management.base import BaseCommand, CommandError

from devices.models import DeviceSnapshot, MonthlyCounterEntry

MILLION_ROLLOVER_SANITY_LIMIT = 500_000
MAX_ROLLOVER_STEPS = 3


class Command(BaseCommand):
    help = "Llena la semana N de MonthlyCounterEntry a partir de DeviceSnapshot."

    def add_arguments(self, parser):
        parser.add_argument("--period", required=True, help="Periodo a actualizar, ej: jul-26")
        parser.add_argument("--week", type=int, required=True, choices=[1, 2, 3, 4, 5])
        parser.add_argument("--start", required=True, help="Fecha inicio (YYYY-MM-DD)")
        parser.add_argument("--end", required=True, help="Fecha fin (YYYY-MM-DD)")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--status",
            default=None,
            help="Filtrar solo impresoras con este status (ej: Instalado).",
        )

    def handle(self, *args, **options):
        period = options["period"]
        week = options["week"]
        dry_run = options["dry_run"]

        try:
            start_date = datetime.date.fromisoformat(options["start"])
            end_date = datetime.date.fromisoformat(options["end"])
        except ValueError as exc:
            raise CommandError(f"Fecha invalida: {exc}")

        counter_field = f"week{week}_counter"
        final_field = f"week{week}_final"
        prev_field = "previous_month_counter" if week == 1 else f"week{week - 1}_counter"

        qs = MonthlyCounterEntry.objects.filter(
            period=period, impresora__isnull=False
        ).select_related("impresora")

        status = options.get("status")
        if status:
            qs = qs.filter(impresora__status=status)

        updated = 0
        no_ip = 0
        no_snapshot = 0
        no_prev = []
        anomalies = []
        corrections = []
        rows = list(qs)

        for entry in rows:
            ip = entry.impresora.ip_address if entry.impresora else ""
            if not ip:
                no_ip += 1
                continue

            snapshot = (
                DeviceSnapshot.objects.filter(
                    ip_address=ip,
                    captured_at__date__gte=start_date,
                    captured_at__date__lte=end_date,
                    page_count__isnull=False,
                )
                .order_by("-captured_at")
                .first()
            )

            if not snapshot:
                no_snapshot += 1
                continue

            raw_counter_value = snapshot.page_count
            counter_value = raw_counter_value
            prev_value = getattr(entry, prev_field)

            if prev_value is None:
                no_prev.append((entry.id, ip))
                final_value = None
            else:
                final_value = counter_value - prev_value
                rollover_steps = 0
                while (
                    final_value < 0
                    and prev_value >= 1_000_000
                    and rollover_steps < MAX_ROLLOVER_STEPS
                ):
                    counter_value += 1_000_000
                    final_value = counter_value - prev_value
                    rollover_steps += 1

                if rollover_steps > 0:
                    if final_value >= 0 and final_value < MILLION_ROLLOVER_SANITY_LIMIT:
                        corrections.append(
                            (entry.id, ip, raw_counter_value, counter_value, final_value)
                        )
                    else:
                        # No quedo en un rango razonable: revertir y marcar anomalia real.
                        counter_value = raw_counter_value
                        final_value = raw_counter_value - prev_value
                        anomalies.append(
                            (entry.id, ip, prev_value, counter_value, final_value)
                        )
                elif final_value < 0:
                    anomalies.append(
                        (entry.id, ip, prev_value, counter_value, final_value)
                    )

            setattr(entry, counter_field, counter_value)
            setattr(entry, final_field, final_value)

            finals = [
                entry.week1_final,
                entry.week2_final,
                entry.week3_final,
                entry.week4_final,
                entry.week5_final,
            ]
            known_finals = [f for f in finals if f is not None]
            entry.monthly_counter = sum(known_finals) if known_finals else None

            if not dry_run:
                entry.save(
                    update_fields=[counter_field, final_field, "monthly_counter"]
                )
            updated += 1

        total_monthly = sum(
            e.monthly_counter or 0 for e in rows if e.monthly_counter is not None
        )

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Semana {week} ({period}): {updated} filas actualizadas de {len(rows)} totales."
            )
        )
        if no_ip:
            self.stdout.write(self.style.WARNING(f"  Sin IP en impresora: {no_ip}"))
        if no_snapshot:
            self.stdout.write(
                self.style.WARNING(
                    f"  Sin DeviceSnapshot entre {start_date} y {end_date}: {no_snapshot}"
                )
            )
        if no_prev:
            self.stdout.write(
                self.style.WARNING(
                    f"  Sin contador de semana anterior ({prev_field}), "
                    f"final quedo en None: {len(no_prev)}"
                )
            )
            for entry_id, ip in no_prev[:20]:
                self.stdout.write(f"    - entry id={entry_id} ip={ip}")

        if corrections:
            self.stdout.write(
                self.style.WARNING(
                    f"  CORRECCION millon truncado (HP Web Jetadmin): {len(corrections)} "
                    f"impresoras (se sumo 1.000.000 x N al valor reportado):"
                )
            )
            for entry_id, ip, raw_value, corrected_value, final_value in corrections:
                self.stdout.write(
                    f"    - entry id={entry_id} ip={ip} reportado={raw_value} "
                    f"corregido={corrected_value} {final_field}={final_value}"
                )

        if anomalies:
            self.stdout.write(
                self.style.ERROR(
                    f"  ANOMALIAS: {len(anomalies)} impresoras con {final_field} negativo "
                    f"(posible reemplazo/reset de contador, revisar manualmente):"
                )
            )
            for entry_id, ip, prev_value, counter_value, final_value in anomalies:
                self.stdout.write(
                    f"    - entry id={entry_id} ip={ip} {prev_field}={prev_value} "
                    f"{counter_field}={counter_value} {final_field}={final_value}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Suma total de monthly_counter para {period}: {total_monthly:,}".replace(",", ".")
            )
        )
