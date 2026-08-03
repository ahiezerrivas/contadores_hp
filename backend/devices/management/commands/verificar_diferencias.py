from django.core.management.base import BaseCommand
from django.db.models import Q

from devices.models import Impresora, MonthlyCounterEntry


class Command(BaseCommand):
    help = "Compara Impresoras Instaladas con contadores mensuales de jul-26"

    def handle(self, *args, **options):
        impresoras_instaladas = Impresora.objects.filter(status="Instalado")
        mensuales_jul26 = MonthlyCounterEntry.objects.filter(
            period="jul-26", printer_status="Instalado"
        )

        self.stdout.write(f"Impresoras con status=Instalado: {impresoras_instaladas.count()}")
        self.stdout.write(f"MonthlyCounterEntry jul-26 con printer_status=Instalado: {mensuales_jul26.count()}")

        # Impresoras Instaladas sin entrada jul-26 Instalado
        impresoras_ids_con_mensual = list(
            mensuales_jul26.values_list("impresora_id", flat=True)
        )
        faltantes = impresoras_instaladas.exclude(id__in=impresoras_ids_con_mensual)

        self.stdout.write(
            self.style.WARNING(
                f"Impresoras Instaladas que NO tienen MonthlyCounterEntry jul-26 Instalado: {faltantes.count()}"
            )
        )

        for imp in faltantes:
            # Buscar si tienen algun mensual jul-26 con otro status
            mensual = MonthlyCounterEntry.objects.filter(
                impresora=imp, period="jul-26"
            ).first()
            if mensual:
                self.stdout.write(
                    f"  - {imp.name} | ip={imp.ip_address or '-'} | serial={imp.serial_number or '-'} | "
                    f"tiene jul-26 con status={mensual.printer_status}"
                )
            else:
                q = Q()
                if imp.ip_address:
                    q |= Q(ip_address=imp.ip_address, period="jul-26")
                if imp.serial_number:
                    q |= Q(serial_number=imp.serial_number, period="jul-26")
                otras = MonthlyCounterEntry.objects.filter(q)
                if otras.exists():
                    self.stdout.write(
                        f"  - {imp.name} | ip={imp.ip_address or '-'} | serial={imp.serial_number or '-'} | "
                        f"sin vinculo, pero con {otras.count()} registro(s) jul-26: "
                        + ", ".join(
                            f"id={o.id} status={o.printer_status} imp={o.impresora_id}"
                            for o in otras
                        )
                    )
                else:
                    self.stdout.write(
                        f"  - {imp.name} | ip={imp.ip_address or '-'} | serial={imp.serial_number or '-'} | "
                        f"sin registro jul-26"
                    )
