from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DeviceSnapshotViewSet,
    ExportRunViewSet,
    ImpresoraViewSet,
    MonthlyCounterEntryViewSet,
    OficinaViewSet,
    LoginView,
    me,
)

router = DefaultRouter()
router.register("runs", ExportRunViewSet, basename="run")
router.register("devices", DeviceSnapshotViewSet, basename="device")
router.register("monthly-counters", MonthlyCounterEntryViewSet, basename="monthly-counter")
router.register("oficinas", OficinaViewSet, basename="oficina")
router.register("impresoras", ImpresoraViewSet, basename="impresora")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", me, name="me"),
] + router.urls
