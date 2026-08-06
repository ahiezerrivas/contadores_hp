"""
Importa los reportes mensuales de contadores (Excel) hacia MonthlyCounterEntry.

Los archivos esperados son del tipo:
    Contador de Pagina Torre Julio del 01 al 31.xlsx
    Contador de Pagina Oficina Julio del 01 al 31.xlsx

Con columnas (en cualquier orden, se detectan por nombre de encabezado):
    Region, Nombre Oficina, Piso, Nombre de Host Sede, Asignada o Ubicacion,
    DisplayName, IPv4Address, SerialNumber, Contador del Mes Anterior,
    Contador Semana 1, Contador Final Semana 1, Contador Semana 2,
    Contador Final Semana 2, Contador Semana 3, Contador Final Semana 3,
    Contador Semana 4, Contador Final Semana 4, Contador Semana 5,
    Contador Final Semana 5, Contador Mensual, Equipos con contadores en 0,
    Fecha, Observaciones, Status Impresora

Uso:
    python manage.py import_counters "Contador de Pagina Torre Julio del 01 al 31.xlsx"
    python manage.py import_counters archivo.xlsx --region Torre --period jul-26
    python manage.py import_counters archivo.xlsx --sheet "Hoja1" --dry-run

Nota: si siempre importas el mismo tipo de archivo, usa los comandos
import_counters_torre / import_counters_oficina, que fijan --region
automaticamente.
"""

from devices.management.commands._counters_import_base import BaseImportCountersCommand


class Command(BaseImportCountersCommand):
    default_region = None
