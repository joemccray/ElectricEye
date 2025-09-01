from rest_framework import viewsets

from .models import GreetingJob
from .serializers import GreetingJobSerializer


class GreetingJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows greeting jobs to be viewed or created.
    """

    queryset = GreetingJob.objects.all().order_by("-created_at")
    serializer_class = GreetingJobSerializer
