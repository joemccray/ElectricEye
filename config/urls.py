from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from integrations.ops.health import healthz
from scans import views

router = routers.DefaultRouter()
router.register(r"scans", views.ScanViewSet)
router.register(r"findings", views.FindingViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("api/", include(router.urls)),
]
