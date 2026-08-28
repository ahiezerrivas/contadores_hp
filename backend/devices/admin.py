from django.contrib import admin, messages
from django.core.management import call_command

from .models import DeviceSnapshot, ExportRun, ExportSchedule, Impresora, MonthlyCounterEntry, Oficina


@admin.register(ExportRun)
class ExportRunAdmin(admin.ModelAdmin):
    list_display = ("id", "executed_at", "total_devices", "success")
    list_filter = ("success",)
    ordering = ("-executed_at",)


@admin.register(DeviceSnapshot)
class DeviceSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "model_name",
        "display_name",
        "ip_address",
        "page_count",
        "device_status_severity",
        "serial_number",
        "system_location",
        "captured_at",
        "run",
    )
    list_filter = ("model_name",)
    search_fields = ("ip_address", "model_name")
    ordering = ("-captured_at",)


@admin.register(ExportSchedule)
class ExportScheduleAdmin(admin.ModelAdmin):
    list_display = ("run_time", "enabled", "updated_at")
    fields = ("enabled", "run_time", "updated_at")
    readonly_fields = ("updated_at",)
    actions = ["ejecutar_ahora"]

    def has_add_permission(self, request):
        # Singleton: solo se permite un registro, creado automaticamente.
        return not ExportSchedule.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        ExportSchedule.get_solo()
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description="Ejecutar export ahora (sin esperar la hora programada)")
    def ejecutar_ahora(self, request, queryset):
        try:
            call_command("run_export", force=True)
            self.message_user(request, "Export ejecutado correctamente.", level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, f"Error al ejecutar el export: {exc}", level=messages.ERROR)


@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "region", "code", "status")
    list_filter = ("status", "region")
    search_fields = ("name", "region", "code")
    ordering = ("name",)


class OficinaAsignadaFilter(admin.SimpleListFilter):
    title = "Oficina asignada"
    parameter_name = "office_asignada"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Con oficina"),
            ("no", "Sin oficina"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(office__isnull=False)
        if self.value() == "no":
            return queryset.filter(office__isnull=True)
        return queryset


class ImpresoraStatusFilter(admin.SimpleListFilter):
    title = "Status impresora"
    parameter_name = "impresora__status"

    def lookups(self, request, model_admin):
        statuses = (
            Impresora.objects.exclude(status="")
            .values_list("status", flat=True)
            .distinct()
        )
        seen = {}
        for s in statuses:
            seen.setdefault(s.lower(), s)
        return sorted((v, v) for v in seen.values())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(impresora__status__iexact=self.value())
        return queryset


@admin.register(MonthlyCounterEntry)
class MonthlyCounterEntryAdmin(admin.ModelAdmin):
    list_display = (
        "impresora_name",
        "impresora_ip",
        "region",
        "category",
        "office__name",
        "impresora",
        "period",
        "monthly_counter",
        "zero_counter_devices",
        "impresora_status",
    )
    list_filter = ("region", "category", "period", ImpresoraStatusFilter, OficinaAsignadaFilter)
    search_fields = ("impresora__ip_address", "impresora__name", "impresora__serial_number", "office__name")
    ordering = ("-period", "region", "office__name")
    fieldsets = (
        (
            "Ubicacion",
            {
                "fields": (
                    "region",
                    "category",
                    "office",
                    "floor",
                    "location",
                )
            },
        ),
        (
            "Dispositivo",
            {"fields": ("impresora",)},
        ),
        (
            "Contadores",
            {
                "fields": (
                    "previous_month_counter",
                    ("week1_counter", "week1_final"),
                    ("week2_counter", "week2_final"),
                    ("week3_counter", "week3_final"),
                    ("week4_counter", "week4_final"),
                    ("week5_counter", "week5_final"),
                    "monthly_counter",
                    "zero_counter_devices",
                )
            },
        ),
        ("Periodo y notas", {"fields": ("period", "observations", "source_file")}),
    )

    @admin.display(description="Nombre", ordering="impresora__name")
    def impresora_name(self, obj):
        return obj.impresora.name if obj.impresora else "-"

    @admin.display(description="IP (del periodo)", ordering="ip_address")
    def impresora_ip(self, obj):
        return obj.ip_address or "-"

    @admin.display(description="Status Impresora (del periodo)", ordering="printer_status")
    def impresora_status(self, obj):
        return obj.printer_status or "-"


@admin.register(Impresora)
class ImpresoraAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "model_name", "ip_address", "serial_number", "status")
    list_filter = ("status",)
    search_fields = ("name", "model_name", "ip_address", "serial_number")
    ordering = ("name",)

