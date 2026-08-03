from django.core.management.base import BaseCommand
from django.db.models import Q

from devices.models import DeviceSnapshot, Impresora, MonthlyCounterEntry


class Command(BaseCommand):
    help = "Crea impresoras maestras y vincula los MonthlyCounterEntry por IP o serial."

    def add_arguments(self, parser):
        parser.add_argument(
            "--detalle-omitidos",
            action="store_true",
            help="Muestra los MonthlyCounterEntry sin IP ni serial",
        )

    def handle(self, *args, **options):
        if options["detalle_omitidos"]:
            omitidos = MonthlyCounterEntry.objects.filter(impresora__isnull=True)
            self.stdout.write(f"Registros sin impresora vinculada: {omitidos.count()}")
            for entry in omitidos:
                imp_name = entry.impresora.name if entry.impresora else "-"
                self.stdout.write(
                    f"  id={entry.id} | display={imp_name} | "
                    f"period={entry.period or '-'}"
                )
            return

        entries = MonthlyCounterEntry.objects.select_related("impresora").all().order_by("-imported_at")
        created = 0
        linked = 0
        skipped = 0

        for entry in entries:
            impresora = entry.impresora
            if impresora:
                continue

            q = Q()
            if entry.impresora_id is None:
                skipped += 1
                continue

            # Ahora usa los datos del objeto anidado para buscar/crear Impresora
            # Si la entrada ya tiene impresora, no hacemos nada.
            # Las entradas sin impresora se vinculan creando o buscando por datos del snapshot.
            ip = ""
            serial = ""

            # Los datos de impresora ahora viven en Impresora; usamos display/ip/serial del snapshot si existe.
            snap = (
                DeviceSnapshot.objects.filter(
                    Q(ip_address__icontains=ip) | Q(serial_number__icontains=serial)
                )
                .order_by("-captured_at")
                .first()
            )

            name = (snap.display_name if snap and snap.display_name else "") or ip or serial or ""
            model_name = (snap.model_name if snap and snap.model_name else "") or ""
            status = (snap.device_status_severity if snap and snap.device_status_severity else "") or ""

            impresora, _ = Impresora.objects.get_or_create(
                ip_address=ip,
                serial_number=serial,
                defaults={
                    "name": name,
                    "model_name": model_name,
                    "status": status,
                },
            )
            created += 1

            entry.impresora = impresora
            entry.save(update_fields=["impresora"])
            linked += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Impresoras creadas: {created}; entradas vinculadas: {linked}; omitidas: {skipped}"
            )
        )
