from rest_framework import viewsets, status
from rest_framework.response import Response

from .serializers import TicketSerializer
from .services import create_ticket


class TicketViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = create_ticket(**serializer.validated_data)
        return Response({"ticket_id": ticket.id}, status=status.HTTP_201_CREATED)
