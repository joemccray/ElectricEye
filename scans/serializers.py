from rest_framework import serializers

from .models import Finding, Scan


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = (
            "id",
            "scan",
            "check_name",
            "resource_id",
            "status",
            "description",
            "created_at",
        )


class ScanSerializer(serializers.ModelSerializer):
    findings = FindingSerializer(many=True, read_only=True)

    class Meta:
        model = Scan
        fields = (
            "id",
            "provider",
            "status",
            "created_at",
            "updated_at",
            "findings",
        )
        read_only_fields = ("status", "findings")
