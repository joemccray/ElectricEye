from celery import shared_task

from .models import GreetingJob


@shared_task
def process_greeting_job(job_id: int) -> None:
    job = GreetingJob.objects.get(id=job_id)
    job.status = "processing"
    job.save(update_fields=["status"])
    # simulate work; in real app integrate services and set real URL
    job.result_url = "https://example.com/out.mp4"
    job.status = "done"
    job.save(update_fields=["result_url", "status"])
