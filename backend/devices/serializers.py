from rest_framework import serializers
from users.models import User

from .models import DeviceSnapshot, ExportRun, Impresora, MonthlyCounterEntry, Oficina


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]


class DeviceSnapshotSerializer(serializers.ModelSerializer):
    is_alert = serializers.SerializerMethodField()

    class Meta:
        model = DeviceSnapshot
        fields = [
            "id",
            "run",
            "model_name",
            "display_name",
            "ip_address",
            "page_count",
            "device_status_severity",
            "serial_number",
            "system_location",
            "captured_at",
            "is_alert",
        ]

    def get_is_alert(self, obj):
        return obj.page_count is None or obj.page_count == 0


class ExportRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportRun
        fields = ["id", "executed_at", "total_devices", "success", "error_message"]


class ExportRunDetailSerializer(ExportRunSerializer):
    snapshots = DeviceSnapshotSerializer(many=True, read_only=True)

    class Meta(ExportRunSerializer.Meta):
        fields = ExportRunSerializer.Meta.fields + ["snapshots"]


class OficinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oficina
        fields = ["id", "name", "status", "region", "code"]


class ImpresoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Impresora
        fields = ["id", "name", "model_name", "ip_address", "serial_number", "status"]


class MonthlyCounterEntrySerializer(serializers.ModelSerializer):
    office_name = serializers.CharField(source="office.name", read_only=True)
    office_status = serializers.CharField(source="office.status", read_only=True)
    impresora = ImpresoraSerializer(read_only=True)

    class Meta:
        model = MonthlyCounterEntry
        fields = [
            "id",
            "region",
            "category",
            "office",
            "office_name",
            "office_status",
            "agency_status",
            "floor",
            "location",
            "ip_address",
            "printer_status",
            "impresora",
            "previous_month_counter",
            "week1_counter",
            "week1_final",
            "week2_counter",
            "week2_final",
            "week3_counter",
            "week3_final",
            "week4_counter",
            "week4_final",
            "week5_counter",
            "week5_final",
            "monthly_counter",
            "zero_counter_devices",
            "period",
            "observations",
            "source_file",
            "imported_at",
        ]

    def update(self, instance, validated_data):
        impresora_data = validated_data.pop("impresora", None)
        instance = super().update(instance, validated_data)
        if impresora_data:
            impresora = instance.impresora or Impresora()
            for attr, value in impresora_data.items():
                setattr(impresora, attr, value)
            impresora.save()
            if instance.impresora_id != impresora.id:
                instance.impresora = impresora
                instance.save(update_fields=["impresora"])
        return instance

    def create(self, validated_data):
        impresora_data = validated_data.pop("impresora", None)
        instance = super().create(validated_data)
        if impresora_data:
            impresora = Impresora.objects.create(**impresora_data)
            instance.impresora = impresora
            instance.save(update_fields=["impresora"])
        return instance
