from django.db import migrations

# Copia fija de los estatus canonicos al momento de esta migracion (no se
# importa desde devices.models para que esta migracion siga siendo estable
# aunque la lista cambie en el futuro).
PRINTER_STATUS_CHOICES = [
    "Instalado",
    "Cierre temporal",
    "Pendiente Retiro",
    "Cierre definitivo",
    "Embalada",
    "Perdida Total",
    "Resguardo en la Agencia",
    "Desistalada",
]


def normalize_all_status_variants(apps, schema_editor):
    Impresora = apps.get_model("devices", "Impresora")
    MonthlyCounterEntry = apps.get_model("devices", "MonthlyCounterEntry")

    for canonical in PRINTER_STATUS_CHOICES:
        Impresora.objects.filter(status__iexact=canonical).exclude(
            status=canonical
        ).update(status=canonical)
        MonthlyCounterEntry.objects.filter(printer_status__iexact=canonical).exclude(
            printer_status=canonical
        ).update(printer_status=canonical)


class Migration(migrations.Migration):
    dependencies = [
        ("devices", "0017_normalize_status_choices"),
    ]

    operations = [
        migrations.RunPython(
            normalize_all_status_variants,
            migrations.RunPython.noop,
        ),
    ]
