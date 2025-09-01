import pytest

from jobs.models import GreetingJob
from jobs.tasks import process_greeting_job


@pytest.mark.django_db
def test_job_reaches_done():
    job = GreetingJob.objects.create(
        first_name="John", voice_id="v1", greeting_seconds=1.5, video_path="/tmp/in.mp4"
    )
    process_greeting_job(
        job.id
    )  # run synchronously in test (CELERY_TASK_ALWAYS_EAGER=True)
    job.refresh_from_db()
    assert job.status == "done"
    assert job.result_url
