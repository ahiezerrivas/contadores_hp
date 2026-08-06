"""
Importa el reporte mensual de contadores de Torre (Excel) hacia
MonthlyCounterEntry. Es un wrapper de import_counters que fija
automaticamente --region "Torre" (se puede sobreescribir con --region).

Uso:
    python manage.py import_counters_torre "Contador de Pagina Torre Julio del 01 al 31.xlsx" --period jul-26
"""

from devices.management.commands._counters_import_base import BaseImportCountersCommand


class Command(BaseImportCountersCommand):
    help = "Importa el reporte mensual de contadores de Torre (Excel) a MonthlyCounterEntry."
    default_region = "Torre"
