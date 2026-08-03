from rest_framework.routers import DefaultRouter

from .views import DeviceSnapshotViewSet, ExportRunViewSet, MonthlyCounterEntryViewSet

router = DefaultRouter()
router.register("runs", ExportRunViewSet, basename="run")
router.register("devices", DeviceSnapshotViewSet, basename="device")
router.register("monthly-counters", MonthlyCounterEntryViewSet, basename="monthly-counter")

urlpatterns = router.urls
