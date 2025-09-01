import pytest
from django.test import Client


@pytest.mark.django_db
def test_healthz_ok():
    c = Client()
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True
