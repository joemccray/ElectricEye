from rest_framework import serializers

from .models import Finding, Scan


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = "__all__"


class ScanSerializer(serializers.ModelSerializer):
    findings = FindingSerializer(many=True, read_only=True)

    class Meta:
        model = Scan
        fields = "__all__"
