from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import GreetingJob
from .tasks import process_greeting_job


@receiver(post_save, sender=GreetingJob)
def enqueue_job(sender, instance: GreetingJob, created: bool, **kwargs):
    if created:
        process_greeting_job.delay(instance.id)
