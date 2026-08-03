"""
Genera las filas "stub" de MonthlyCounterEntry para un nuevo periodo (mes),
usando como base el ultimo periodo existente de cada impresora.

Para cada Impresora:
  - Si ya tiene una fila en --period, no se toca (evita duplicados).
  - Si tiene una fila en un periodo anterior (el mas reciente encontrado,
    o el indicado con --source-period), se copia region/office/floor/location
    y se usa el ultimo contador conocido de esa fila anterior
    (el mayor de week5_counter..week1_counter, o previous_month_counter si
    ninguna semana tiene dato) como previous_month_counter del nuevo periodo.
  - Si nunca ha tenido una fila (impresora nueva, recien agregada a HP Web
    Jetadmin), se crea usando el ultimo DeviceSnapshot.page_count disponible
    (si existe) como previous_month_counter, y region/office vacios.

No se filtra por status de la impresora: una impresora "Cierre temporal"
este mes puede volver a estar activa el siguiente, asi que se genera la fila
para todas.

Uso:
    python manage.py generar_periodo_mensual --period ago-26 --dry-run
    python manage.py generar_periodo_mensual --period ago-26
    python manage.py generar_periodo_mensual --period ago-26 --source-period jul-26
"""

from django.core.management.base import BaseCommand

from devices.models import DeviceSnapshot, Impresora, MonthlyCounterEntry
from devices.utils import period_sort_key

WEEK_FIELDS_DESC = [
    "week5_counter",
    "week4_counter",
    "week3_counter",
    "week2_counter",
    "week1_counter",
    "previous_month_counter",
]


def last_known_counter(entry):
    for field in WEEK_FIELDS_DESC:
        value = getattr(entry, field)
        if value is not None:
            return value
    return None


class Command(BaseCommand):
    help = "Crea las filas MonthlyCounterEntry stub de un nuevo periodo a partir del periodo anterior."

    def add_arguments(self, parser):
        parser.add_argument("--period", required=True, help="Periodo nuevo a generar, ej: ago-26")
        parser.add_argument(
            "--source-period",
            default=None,
            help="Periodo del cual copiar los datos base. Por defecto se usa el periodo "
            "cronologicamente mas reciente que exista antes de --period.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        target_period = options["period"]
        source_period_arg = options.get("source_period")
        dry_run = options["dry_run"]

        existing_target_impresora_ids = set(
            MonthlyCounterEntry.objects.filter(period=target_period, impresora__isnull=False)
            .values_list("impresora_id", flat=True)
        )

        created_from_source = 0
        created_new_device = 0
        skipped_existing = 0
        skipped_no_data = []

        all_impresoras = list(Impresora.objects.all())

        for impresora in all_impresoras:
            if impresora.id in existing_target_impresora_ids:
                skipped_existing += 1
                continue

            entries = list(
                MonthlyCounterEntry.objects.filter(impresora=impresora).exclude(period=target_period)
            )

            source_entry = None
            if entries:
                if source_period_arg:
                    source_entry = next(
                        (e for e in entries if e.period == source_period_arg), None
                    )
                else:
                    entries.sort(key=lambda e: period_sort_key(e.period), reverse=True)
                    candidates = [e for e in entries if period_sort_key(e.period) < period_sort_key(target_period)]
                    source_entry = candidates[0] if candidates else entries[0]

            if source_entry:
                previous_counter = last_known_counter(source_entry)
                new_entry = MonthlyCounterEntry(
                    region=source_entry.region,
                    office=source_entry.office,
                    floor=source_entry.floor,
                    location=source_entry.location,
                    impresora=impresora,
                    previous_month_counter=previous_counter,
                    period=target_period,
                    source_file=f"generado automaticamente desde {source_entry.period}",
                )
                if not dry_run:
                    new_entry.save()
                created_from_source += 1
            else:
                last_snapshot = (
                    DeviceSnapshot.objects.filter(
                        ip_address=impresora.ip_address, page_count__isnull=False
                    )
                    .order_by("-captured_at")
                    .first()
                    if impresora.ip_address
                    else None
                )
                if not last_snapshot:
                    skipped_no_data.append((impresora.id, impresora.ip_address, impresora.name))

                new_entry = MonthlyCounterEntry(
                    impresora=impresora,
                    previous_month_counter=last_snapshot.page_count if last_snapshot else None,
                    period=target_period,
                    source_file="generado automaticamente (impresora nueva, sin periodo anterior)",
                )
                if not dry_run:
                    new_entry.save()
                created_new_device += 1

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Periodo {target_period}: "
                f"{created_from_source} creadas desde periodo anterior, "
                f"{created_new_device} creadas como impresora nueva, "
                f"{skipped_existing} ya existian."
            )
        )
        if skipped_no_data:
            self.stdout.write(
                self.style.WARNING(
                    f"  Impresoras nuevas sin DeviceSnapshot (previous_month_counter quedo en None): "
                    f"{len(skipped_no_data)}"
                )
            )
            for imp_id, ip, name in skipped_no_data:
                self.stdout.write(f"    - impresora id={imp_id} ip={ip} name={name}")
