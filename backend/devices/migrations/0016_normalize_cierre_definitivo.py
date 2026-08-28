from django.db import migrations


def normalize_cierre_definitivo(apps, schema_editor):
    Impresora = apps.get_model("devices", "Impresora")
    MonthlyCounterEntry = apps.get_model("devices", "MonthlyCounterEntry")

    Impresora.objects.filter(status__iexact="cierre definitivo").update(
        status="Cierre definitivo"
    )
    MonthlyCounterEntry.objects.filter(printer_status__iexact="cierre definitivo").update(
        printer_status="Cierre definitivo"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("devices", "0015_monthlycounterentry_category"),
    ]

    operations = [
        migrations.RunPython(
            normalize_cierre_definitivo,
            migrations.RunPython.noop,
        ),
    ]
