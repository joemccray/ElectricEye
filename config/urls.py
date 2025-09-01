from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from integrations.ops.health import healthz
from scans import views as scan_views
from jobs import views as job_views
from agents import views as agent_views
from billing import webhooks as billing_webhooks
from support import views as support_views

router = routers.DefaultRouter()
router.register(r"scans", scan_views.ScanViewSet)
router.register(r"findings", scan_views.FindingViewSet)
router.register(r"jobs", job_views.GreetingJobViewSet)
router.register(r"agents", agent_views.AgentViewSet)
router.register(r"tasks", agent_views.TaskViewSet)
router.register(r"crews", agent_views.CrewViewSet)
router.register(r"agent-jobs", agent_views.JobViewSet)
router.register(r"support-tickets", support_views.TicketViewSet, basename="support-ticket")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("api/", include(router.urls)),
    path("billing/stripe/webhook/", billing_webhooks.stripe_webhook, name="stripe-webhook"),
]
