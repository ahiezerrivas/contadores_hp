from django.db import models
from django.utils import timezone


class ExportRun(models.Model):
    """Representa una ejecucion del export desde HP Web Jetadmin (SQL Server)."""

    executed_at = models.DateTimeField(auto_now_add=True)
    total_devices = models.PositiveIntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"Run {self.executed_at:%Y-%m-%d %H:%M:%S} ({self.total_devices} dispositivos)"


class DeviceSnapshot(models.Model):
    """Foto de un dispositivo en un momento dado (una fila por dispositivo por run)."""

    run = models.ForeignKey(ExportRun, related_name="snapshots", on_delete=models.CASCADE)
    model_name = models.CharField(max_length=255, blank=True, default="")
    display_name = models.CharField(max_length=255, blank=True, default="")
    ip_address = models.CharField(max_length=45, blank=True, default="")
    page_count = models.BigIntegerField(null=True, blank=True)
    device_status_severity = models.CharField(max_length=50, blank=True, default="")
    serial_number = models.CharField(max_length=100, blank=True, default="")
    system_location = models.CharField(max_length=255, blank=True, default="")
    captured_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["model_name", "ip_address"]
        indexes = [
            models.Index(fields=["ip_address", "captured_at"]),
            models.Index(fields=["run", "ip_address"]),
        ]

    def __str__(self):
        return f"{self.model_name} ({self.ip_address}) - {self.page_count}"


class ExportSchedule(models.Model):
    """Configuracion (singleton) de la hora en que se ejecuta el export automaticamente."""

    enabled = models.BooleanField(
        default=True, help_text="Si esta desactivado, el export no se ejecutara automaticamente."
    )
    run_time = models.TimeField(
        help_text="Hora del dia (servidor) en la que se ejecuta el export automaticamente."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracion de horario"
        verbose_name_plural = "Configuracion de horario"

    def __str__(self):
        estado = "activo" if self.enabled else "inactivo"
        return f"Export automatico a las {self.run_time} ({estado})"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"run_time": "07:00"})
        return obj

    @classmethod
    def should_run(cls):
        schedule = cls.get_solo()
        if not schedule.enabled:
            return False
        now = timezone.localtime()
        return now.time() >= schedule.run_time


class Oficina(models.Model):
    """Catalogo de oficinas para relacionar con los contadores mensuales."""

    name = models.CharField("Nombre de la Oficina", max_length=255, blank=True, default="")
    status = models.CharField(
        "Estatus",
        max_length=20,
        choices=[("Activo", "Activo"), ("Inactivo", "Inactivo")],
        default="Activo",
    )
    region = models.CharField("Region", max_length=100, blank=True, default="")
    code = models.CharField("Codigo de Oficina", max_length=50, blank=True, default="")

    class Meta:
        verbose_name = "Oficina"
        verbose_name_plural = "Oficinas"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Impresora(models.Model):
    """Catalogo maestro de impresoras."""

    name = models.CharField("Nombre", max_length=255, blank=True, default="")
    model_name = models.CharField("Modelo", max_length=255, blank=True, default="")
    ip_address = models.CharField("IP", max_length=45, blank=True, default="")
    serial_number = models.CharField(
        "Serial", max_length=100, unique=True, null=True, blank=True, default=None
    )
    status = models.CharField("Status", max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "Impresora"
        verbose_name_plural = "Impresoras"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MonthlyCounterEntry(models.Model):
    """Registro mensual de contadores por dispositivo, cargado manualmente (admin)
    o importado desde los reportes en Excel (Contador de Pagina Torre/Oficina).
    Una fila = un dispositivo en un periodo (mes) determinado.
    """

    region = models.CharField(max_length=100, blank=True, default="")
    office = models.ForeignKey(
        Oficina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Nombre Oficina",
        related_name="monthly_entries",
    )
    floor = models.CharField("Piso", max_length=100, blank=True, default="")
    location = models.CharField("Asignada o Ubicacion", max_length=255, blank=True, default="")
    impresora = models.ForeignKey(
        Impresora,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Impresora",
        related_name="monthly_entries",
    )

    previous_month_counter = models.BigIntegerField(
        "Contador del Mes Anterior", null=True, blank=True
    )

    week1_counter = models.BigIntegerField("Contador Semana 1", null=True, blank=True)
    week1_final = models.BigIntegerField("Contador Final Semana 1", null=True, blank=True)
    week2_counter = models.BigIntegerField("Contador Semana 2", null=True, blank=True)
    week2_final = models.BigIntegerField("Contador Final Semana 2", null=True, blank=True)
    week3_counter = models.BigIntegerField("Contador Semana 3", null=True, blank=True)
    week3_final = models.BigIntegerField("Contador Final Semana 3", null=True, blank=True)
    week4_counter = models.BigIntegerField("Contador Semana 4", null=True, blank=True)
    week4_final = models.BigIntegerField("Contador Final Semana 4", null=True, blank=True)
    week5_counter = models.BigIntegerField("Contador Semana 5", null=True, blank=True)
    week5_final = models.BigIntegerField("Contador Final Semana 5", null=True, blank=True)

    monthly_counter = models.BigIntegerField("Contador Mensual", null=True, blank=True)
    zero_counter_devices = models.IntegerField(
        "Equipos con contadores en 0", null=True, blank=True
    )
    period = models.CharField(
        "Fecha", max_length=20, blank=True, default="", help_text="Ej: jun-26"
    )
    observations = models.TextField("Observaciones", blank=True, default="")

    source_file = models.CharField(max_length=255, blank=True, default="")
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contador mensual"
        verbose_name_plural = "Contadores mensuales"
        ordering = ["-imported_at"]
        indexes = [
            models.Index(fields=["impresora", "period"]),
            models.Index(fields=["region", "period"]),
        ]

    def __str__(self):
        nombre = self.impresora.name if self.impresora else ""
        ip = self.impresora.ip_address if self.impresora else ""
        return f"{nombre} ({ip}) - {self.period}"
