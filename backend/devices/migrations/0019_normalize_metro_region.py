import re

from django.db import migrations

_METRO_REGION_RE = re.compile(r"^metro\s+[ivxlcdm]+$", re.IGNORECASE)


def normalize_metro_region(apps, schema_editor):
    MonthlyCounterEntry = apps.get_model("devices", "MonthlyCounterEntry")

    regions = (
        MonthlyCounterEntry.objects.exclude(region="")
        .order_by()
        .values_list("region", flat=True)
        .distinct()
    )
    for region in regions:
        if region and _METRO_REGION_RE.match(region.strip()) and region != "Metro":
            MonthlyCounterEntry.objects.filter(region=region).update(region="Metro")


class Migration(migrations.Migration):
    dependencies = [
        ("devices", "0018_normalize_all_status_variants"),
    ]

    operations = [
        migrations.RunPython(
            normalize_metro_region,
            migrations.RunPython.noop,
        ),
    ]
