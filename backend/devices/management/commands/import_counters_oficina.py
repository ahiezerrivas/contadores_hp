"""
Importa el reporte mensual de contadores de Oficina (Excel) hacia
MonthlyCounterEntry. Es un wrapper de import_counters que fija
automaticamente --category "Oficina" (se puede sobreescribir con --category).

Uso:
    python manage.py import_counters_oficina "Contador de Pagina Oficina Julio del 01 al 31.xlsx" --period jul-26
"""

from devices.management.commands._counters_import_base import BaseImportCountersCommand


class Command(BaseImportCountersCommand):
    help = "Importa el reporte mensual de contadores de Oficina (Excel) a MonthlyCounterEntry."
    default_category = "Oficina"
