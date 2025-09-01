from django.db import transaction
from rest_framework import viewsets

from .models import Finding, Scan
from .serializers import FindingSerializer, ScanSerializer
from .tasks import run_scan


class ScanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows scans to be viewed or edited.
    """

    queryset = Scan.objects.all().order_by("-created_at")
    serializer_class = ScanSerializer

    def perform_create(self, serializer):
        scan = serializer.save()
        transaction.on_commit(lambda: run_scan.delay(scan.id))


class FindingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows findings to be viewed.
    """

    queryset = Finding.objects.all().order_by("-created_at")
    serializer_class = FindingSerializer
