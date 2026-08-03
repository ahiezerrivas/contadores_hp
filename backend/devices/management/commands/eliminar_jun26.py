from django.core.management.base import BaseCommand

from devices.models import MonthlyCounterEntry


class Command(BaseCommand):
    help = "Elimina todos los contadores mensuales del periodo jun-26."

    def handle(self, *args, **options):
        qs = MonthlyCounterEntry.objects.filter(period="jun-26")
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No hay registros con periodo jun-26."))
            return
        self.stdout.write(f"Eliminando {count} registro(s) con periodo jun-26...")
        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Eliminados {deleted} registro(s)."))
