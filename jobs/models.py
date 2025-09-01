from django.db import models


class GreetingJob(models.Model):
    first_name = models.CharField(max_length=100)
    voice_id = models.CharField(max_length=100)
    greeting_seconds = models.FloatField()
    video_path = models.CharField(max_length=500)
    status = models.CharField(max_length=12, default="queued")
    result_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
