from rest_framework import serializers


class TicketSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    description = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
