from celery import shared_task

from .models import GreetingJob
from .services import generate_greeting


@shared_task(ignore_result=True)
def process_greeting_job(job_id: int) -> None:
    job = GreetingJob.objects.get(id=job_id)
    if job.status != "queued":
        return

    job.status = "processing"
    job.save(update_fields=["status"])

    job.greeting_message = generate_greeting(job.first_name)
    job.status = "done"
    job.save(update_fields=["greeting_message", "status"])
