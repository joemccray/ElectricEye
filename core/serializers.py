from rest_framework import serializers


class CreateGreetingRequestSer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    voice_id = serializers.CharField(max_length=100)
    greeting_seconds = serializers.FloatField(min_value=0)
    video_path = serializers.CharField()


class CreateGreetingResponseSer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["queued", "processing", "done", "failed"])
