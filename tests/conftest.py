import os
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .helpers.http_block import _block_external_http  # noqa: F401

@pytest.fixture(autouse=True, scope="session")
def _env_for_tests():
    os.environ.setdefault("DJANGO_ENV", "test")
    os.environ.setdefault("ALLOW_DESTRUCTIVE", "0")
    os.environ.setdefault("NO_EXTERNAL_HTTP", "1")
    yield

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="tester", email="tester@example.com", password="password")

@pytest.fixture
def authed(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
