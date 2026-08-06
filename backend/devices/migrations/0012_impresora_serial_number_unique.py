from django.db import migrations, models


def merge_duplicate_serials(apps, schema_editor):
    """Antes de hacer serial_number unico, fusiona los Impresora duplicados
    que compartan el mismo serial (dejando el que tenga datos mas completos)
    y reasigna los MonthlyCounterEntry que apuntaban al duplicado eliminado."""
    Impresora = apps.get_model("devices", "Impresora")
    MonthlyCounterEntry = apps.get_model("devices", "MonthlyCounterEntry")

    seen = {}
    for imp in Impresora.objects.exclude(serial_number="").order_by("id"):
        key = imp.serial_number
        if key not in seen:
            seen[key] = imp
            continue

        keeper = seen[key]
        duplicate = imp

        # Prefiere como "keeper" el registro cuyo name sea distinto del
        # model_name (indicio de que tiene el nombre de host real, no el
        # modelo duplicado por el bug de mapeo de columnas del importador).
        if duplicate.name and duplicate.name != duplicate.model_name and (
            not keeper.name or keeper.name == keeper.model_name
        ):
            keeper, duplicate = duplicate, keeper
            seen[key] = keeper

        MonthlyCounterEntry.objects.filter(impresora_id=duplicate.id).update(
            impresora_id=keeper.id
        )
        duplicate.delete()


def null_out_empty_serials(apps, schema_editor):
    Impresora = apps.get_model("devices", "Impresora")
    Impresora.objects.filter(serial_number="").update(serial_number=None)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    # Postgres no permite ALTER TABLE sobre devices_impresora en la misma
    # transaccion donde se borraron filas de esa tabla (quedan triggers de
    # FK pendientes por MonthlyCounterEntry.impresora). Se desactiva la
    # atomicidad para que cada operacion corra en su propia transaccion.
    atomic = False

    dependencies = [
        ("devices", "0011_remove_monthlycounterentry_devices_mon_ip_addr_1e23dd_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="impresora",
            name="serial_number",
            field=models.CharField(
                "Serial", max_length=100, null=True, blank=True, default=None
            ),
        ),
        migrations.RunPython(merge_duplicate_serials, reverse_noop),
        migrations.RunPython(null_out_empty_serials, reverse_noop),
        migrations.AlterField(
            model_name="impresora",
            name="serial_number",
            field=models.CharField(
                "Serial", max_length=100, unique=True, null=True, blank=True, default=None
            ),
        ),
    ]
