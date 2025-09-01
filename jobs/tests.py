import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import GreetingJob
from .tasks import process_greeting_job


@pytest.mark.django_db
def test_greeting_job_creation():
    job = GreetingJob.objects.create(
        first_name="John",
        voice_id="v1",
        greeting_seconds=1.5,
        video_path="/tmp/in.mp4",
    )
    assert job.first_name == "John"
    assert job.status == "queued"
    assert str(job) == f"GreetingJob {job.id}"


@pytest.mark.django_db
def test_process_greeting_job_task():
    job = GreetingJob.objects.create(
        first_name="John",
        voice_id="v1",
        greeting_seconds=1.5,
        video_path="/tmp/in.mp4",
    )
    process_greeting_job(job.id)
    job.refresh_from_db()
    assert job.status == "done"
    assert job.greeting_message == "Hello, John! Welcome to our platform."


@pytest.mark.django_db
def test_create_greeting_job_api():
    client = APIClient()
    url = reverse("greetingjob-list")
    data = {
        "first_name": "Jane",
        "voice_id": "v2",
        "greeting_seconds": 2.0,
        "video_path": "/tmp/in2.mp4",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert GreetingJob.objects.count() == 1
    job = GreetingJob.objects.first()
    assert job.first_name == "Jane"
    assert job.status == "queued"


@pytest.mark.django_db
def test_list_greeting_jobs_api():
    client = APIClient()
    GreetingJob.objects.create(
        first_name="Jane",
        voice_id="v2",
        greeting_seconds=2.0,
        video_path="/tmp/in2.mp4",
    )
    GreetingJob.objects.create(
        first_name="John",
        voice_id="v1",
        greeting_seconds=1.5,
        video_path="/tmp/in.mp4",
    )
    url = reverse("greetingjob-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
@patch("jobs.tasks.generate_greeting")
def test_process_greeting_job_idempotency(mock_generate_greeting):
    job = GreetingJob.objects.create(
        first_name="John",
        voice_id="v1",
        greeting_seconds=1.5,
        video_path="/tmp/in.mp4",
    )
    process_greeting_job(job.id)
    process_greeting_job(job.id)
    mock_generate_greeting.assert_called_once_with("John")
