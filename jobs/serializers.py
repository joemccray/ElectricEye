from rest_framework import serializers

from .models import GreetingJob


class GreetingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = GreetingJob
        fields = (
            "id",
            "first_name",
            "voice_id",
            "greeting_seconds",
            "video_path",
            "status",
            "result_url",
            "greeting_message",
            "created_at",
        )
        read_only_fields = ("status", "greeting_message", "result_url")
