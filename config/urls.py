from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from scans import views
from integrations.ops.health import healthz

router = routers.DefaultRouter()
router.register(r'scans', views.ScanViewSet)
router.register(r'findings', views.FindingViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', healthz),
    path('api/', include(router.urls)),
]
