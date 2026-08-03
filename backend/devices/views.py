import ipaddress
import platform
import re
import subprocess

from django.core.management import call_command
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DeviceSnapshot, ExportRun, Impresora, MonthlyCounterEntry, Oficina
from .serializers import (
    DeviceSnapshotSerializer,
    ExportRunDetailSerializer,
    ExportRunSerializer,
    MonthlyCounterEntrySerializer,
)
from .utils import period_sort_key


class DeviceSnapshotFilter(filters.FilterSet):
    model_name = filters.CharFilter(field_name="model_name", lookup_expr="icontains")
    ip_address = filters.CharFilter(field_name="ip_address", lookup_expr="icontains")
    run = filters.NumberFilter(field_name="run_id")
    captured_at_after = filters.DateFilter(field_name="captured_at", lookup_expr="date__gte")
    captured_at_before = filters.DateFilter(field_name="captured_at", lookup_expr="date__lte")

    class Meta:
        model = DeviceSnapshot
        fields = ["model_name", "ip_address", "run", "captured_at_after", "captured_at_before"]


class ExportRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExportRun.objects.all()
    serializer_class = ExportRunSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ExportRunDetailSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"])
    def latest(self, request):
        run = ExportRun.objects.filter(success=True).order_by("-executed_at").first()
        if not run:
            return Response({})
        serializer = ExportRunDetailSerializer(run)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def trigger(self, request):
        """Ejecuta el export (SQL Server -> Postgres) al instante y devuelve el nuevo run."""
        before_id = (
            ExportRun.objects.order_by("-id").values_list("id", flat=True).first() or 0
        )
        call_command("run_export", force=True)
        run = ExportRun.objects.filter(id__gt=before_id).order_by("-id").first()
        if not run:
            return Response({"detail": "No se pudo ejecutar el export."}, status=500)
        serializer = ExportRunDetailSerializer(run)
        status_code = 201 if run.success else 502
        return Response(serializer.data, status=status_code)


class DeviceSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeviceSnapshot.objects.select_related("run").all()
    serializer_class = DeviceSnapshotSerializer
    filterset_class = DeviceSnapshotFilter

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Snapshots del ultimo run exitoso (estado actual de cada dispositivo)."""
        run = ExportRun.objects.filter(success=True).order_by("-executed_at").first()
        if not run:
            return Response([])
        qs = self.filter_queryset(run.snapshots.all())
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def alerts(self, request):
        """Dispositivos del ultimo run con page_count en 0 o nulo."""
        run = ExportRun.objects.filter(success=True).order_by("-executed_at").first()
        if not run:
            return Response([])
        qs = run.snapshots.filter(Q(page_count__isnull=True) | Q(page_count=0))
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def history(self, request):
        """Historico de un dispositivo por IP, ordenado por fecha, para graficar tendencia.

        Cada entrada incluye ``printed_since_previous``: la diferencia de ``page_count``
        respecto a la captura anterior (paginas impresas entre ambas fechas).
        """
        ip_address = request.query_params.get("ip_address")
        if not ip_address:
            return Response({"detail": "ip_address es requerido"}, status=400)
        qs = (
            DeviceSnapshot.objects.filter(ip_address=ip_address)
            .select_related("run")
            .order_by("captured_at")
        )
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        prev_page_count = None
        for item in data:
            page_count = item["page_count"]
            if prev_page_count is None or page_count is None:
                item["printed_since_previous"] = None
            else:
                item["printed_since_previous"] = page_count - prev_page_count
            if page_count is not None:
                prev_page_count = page_count
        return Response(data)

    @action(detail=False, methods=["get"])
    def weekly(self, request):
        """Resumen semanal por dispositivo."""
        date_param = request.query_params.get("date")
        if date_param:
            date_obj = parse_date(date_param)
            if not date_obj:
                return Response({"detail": "date debe tener formato YYYY-MM-DD"}, status=400)
        else:
            date_obj = timezone.localtime().date()

        week_start = date_obj - timezone.timedelta(days=date_obj.weekday())
        week_end = week_start + timezone.timedelta(days=6)

        qs = (
            DeviceSnapshot.objects.filter(
                captured_at__date__gte=week_start,
                captured_at__date__lte=week_end,
            )
            .select_related("run")
            .order_by("ip_address", "captured_at")
        )

        devices = {}
        for snap in qs:
            ip = snap.ip_address
            if ip not in devices:
                devices[ip] = {
                    "ip_address": ip,
                    "model_name": snap.model_name,
                    "display_name": snap.display_name,
                    "serial_number": snap.serial_number,
                    "days_total": 0,
                    "days_at_zero": 0,
                    "last_page_count": snap.page_count,
                    "last_captured_at": snap.captured_at,
                    "max_page_count": snap.page_count or 0,
                }
            devices[ip]["days_total"] += 1
            if snap.page_count is None or snap.page_count == 0:
                devices[ip]["days_at_zero"] += 1
            devices[ip]["last_page_count"] = snap.page_count
            devices[ip]["last_captured_at"] = snap.captured_at
            if snap.page_count and snap.page_count > devices[ip]["max_page_count"]:
                devices[ip]["max_page_count"] = snap.page_count

        result = sorted(
            [{**data, "is_alert": data["days_at_zero"] > 0} for data in devices.values()],
            key=lambda x: (x["days_at_zero"], x["ip_address"]),
            reverse=True,
        )

        return Response({
            "week_start": week_start,
            "week_end": week_end,
            "date": date_obj,
            "devices": result,
        })

    @action(detail=False, methods=["get"])
    def ping(self, request):
        """Hace ping (ICMP) a una IP desde el servidor backend.

        El navegador no puede hacer ping directamente por seguridad, por eso
        esta llamada la ejecuta el backend (que si tiene acceso a la red de
        impresoras) y devuelve si respondio o no.
        """
        ip_address = request.query_params.get("ip_address", "")
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return Response({"detail": "ip_address invalida"}, status=400)

        is_windows = platform.system().lower() == "windows"
        count_flag = "-n" if is_windows else "-c"
        timeout_flag = "-w" if is_windows else "-W"
        timeout_value = "1000" if is_windows else "1"

        try:
            completed = subprocess.run(
                ["ping", count_flag, "1", timeout_flag, timeout_value, ip_address],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = completed.stdout
            # No basta con el returncode: en Windows, si un router intermedio
            # responde "TTL expirado en transito" (TTL expired), ping.exe
            # cuenta eso como "recibido" y termina con exit code 0, aunque el
            # destino real nunca respondio. Se valida que la respuesta venga
            # efectivamente desde la IP destino.
            pattern = re.compile(
                rf"(desde|from)\s+{re.escape(ip_address)}\b", re.IGNORECASE
            )
            reachable = completed.returncode == 0 and bool(pattern.search(output))
        except Exception as exc:
            return Response(
                {"ip_address": ip_address, "reachable": False, "error": str(exc)}
            )

        return Response(
            {"ip_address": ip_address, "reachable": reachable, "output": output}
        )


class MonthlyCounterEntryFilter(filters.FilterSet):
    region = filters.CharFilter(field_name="region")
    period = filters.CharFilter(field_name="period")
    printer_status = filters.CharFilter(field_name="impresora__status")
    search = filters.CharFilter(method="filter_search")
    office = filters.NumberFilter(field_name="office_id")

    class Meta:
        model = MonthlyCounterEntry
        fields = ["region", "period", "printer_status", "office"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(impresora__ip_address__icontains=value)
            | Q(impresora__name__icontains=value)
            | Q(impresora__serial_number__icontains=value)
            | Q(office__name__icontains=value)
        )


class MonthlyCounterEntryViewSet(viewsets.ModelViewSet):
    queryset = MonthlyCounterEntry.objects.all()
    serializer_class = MonthlyCounterEntrySerializer
    filterset_class = MonthlyCounterEntryFilter
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        ("impresora__name", "display_name"),
        ("impresora__ip_address", "ip_address"),
        ("impresora__serial_number", "serial_number"),
        "region",
        "office__name",
        "office__status",
        "period",
        "monthly_counter",
        ("impresora__status", "printer_status"),
    ]

    def filter_queryset(self, queryset):
        """Aplica filtros y ordena cronologicamente por period cuando se pide."""
        for backend in list(self.filter_backends):
            if backend is not OrderingFilter:
                queryset = backend().filter_queryset(self.request, queryset, self)

        ordering = self.request.query_params.get("ordering", "")
        if ordering and "period" in ordering:
            desc = ordering.startswith("-")
            return sorted(queryset, key=lambda obj: period_sort_key(obj.period), reverse=desc)

        return OrderingFilter().filter_queryset(self.request, queryset, self)

    def _filtered_queryset(self, request, exclude=None):
        qs = MonthlyCounterEntry.objects.all()
        region = request.query_params.get("region")
        if region and region != "__all__" and exclude != "region":
            qs = qs.filter(region=region)
        period = request.query_params.get("period")
        if period and period != "__all__" and exclude != "period":
            qs = qs.filter(period=period)
        printer_status = request.query_params.get("printer_status")
        if printer_status and printer_status != "__all__" and exclude != "printer_status":
            qs = qs.filter(impresora__status=printer_status)
        office = request.query_params.get("office")
        if office and office != "__all__" and exclude != "office":
            qs = qs.filter(office_id=office)
        return qs

    @action(detail=False, methods=["get"])
    def filters(self, request):
        """Valores distintos disponibles para armar los filtros del front."""
        # order_by() limpia el ordering por defecto del modelo (-imported_at); si no se
        # limpia, Django incluye esa columna en el SELECT DISTINCT y el resultado deja
        # de ser realmente distinto por region/period/printer_status.
        regions = sorted(
            self._filtered_queryset(request, exclude="region")
            .exclude(region="")
            .order_by()
            .values_list("region", flat=True)
            .distinct()
        )
        periods = sorted(
            self._filtered_queryset(request, exclude="period")
            .exclude(period="")
            .order_by()
            .values_list("period", flat=True)
            .distinct(),
            key=period_sort_key,
            reverse=True,
        )
        printer_statuses = sorted(
            self._filtered_queryset(request, exclude="printer_status")
            .exclude(impresora__status="")
            .order_by()
            .values_list("impresora__status", flat=True)
            .distinct()
        )
        office_qs = self._filtered_queryset(request, exclude="office")
        offices = list(
            Oficina.objects.filter(
                monthly_entries__id__in=office_qs.values_list("id", flat=True)
            )
            .distinct()
            .order_by("name")
            .values("id", "name")
        )
        return Response({
            "regions": regions,
            "periods": periods,
            "printer_statuses": printer_statuses,
            "offices": offices,
        })

    @action(detail=False, methods=["patch"], url_path="impresora-status")
    def impresora_status(self, request):
        """Actualiza el status de una Impresora directamente (usado desde la
        alerta de 'sin lectura reciente' para poder marcar, por ejemplo,
        'Retirado' sin tener que entrar al detalle completo del contador)."""
        impresora_id = request.data.get("impresora_id")
        status_value = request.data.get("status")
        if not impresora_id or status_value is None:
            return Response(
                {"detail": "impresora_id y status son requeridos"}, status=400
            )
        try:
            impresora = Impresora.objects.get(id=impresora_id)
        except Impresora.DoesNotExist:
            return Response({"detail": "Impresora no encontrada"}, status=404)

        impresora.status = status_value
        impresora.save(update_fields=["status"])
        return Response({"id": impresora.id, "status": impresora.status})

    @action(detail=False, methods=["get"])
    def missing_snapshots(self, request):
        """Impresoras vinculadas a MonthlyCounterEntry que no tienen ningun
        DeviceSnapshot con page_count valido en el rango de dias reciente.

        Query params:
            days: tamano de la ventana en dias, contando desde hoy hacia atras
                  (default 5).
            period, printer_status, region, office: mismos filtros que el listado.
        """
        try:
            days = int(request.query_params.get("days", 5))
        except ValueError:
            days = 5
        days = max(1, days)

        end_date = timezone.localtime().date()
        start_date = end_date - timezone.timedelta(days=days - 1)

        qs = self._filtered_queryset(request).filter(impresora__isnull=False).select_related(
            "impresora", "office"
        )

        results = []
        seen_keys = set()
        for entry in qs:
            impresora = entry.impresora
            ip = impresora.ip_address

            # Deduplicar por IP (puede haber registros Impresora duplicados
            # con la misma IP) y, si no hay IP, por id de impresora.
            dedup_key = ip or f"impresora-{impresora.id}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            if not ip:
                last_snapshot = None
                has_recent = False
            else:
                has_recent = DeviceSnapshot.objects.filter(
                    ip_address=ip,
                    captured_at__date__gte=start_date,
                    captured_at__date__lte=end_date,
                    page_count__isnull=False,
                ).exists()
                last_snapshot = (
                    DeviceSnapshot.objects.filter(ip_address=ip)
                    .order_by("-captured_at")
                    .first()
                    if not has_recent
                    else None
                )

            if has_recent:
                continue

            results.append({
                "monthly_counter_id": entry.id,
                "impresora_id": impresora.id,
                "ip_address": ip,
                "name": impresora.name,
                "printer_status": impresora.status,
                "office_name": entry.office.name if entry.office else "",
                "region": entry.region,
                "period": entry.period,
                "last_captured_at": last_snapshot.captured_at if last_snapshot else None,
                "last_page_count": last_snapshot.page_count if last_snapshot else None,
            })

        results.sort(key=lambda r: (r["office_name"] or "", r["name"] or ""))

        return Response({
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "count": len(results),
            "results": results,
        })
