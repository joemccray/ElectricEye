import pytest
from django.urls import reverse
from rest_framework import status

from .models import Agent


@pytest.mark.django_db
def test_agent_creation():
    agent = Agent.objects.create(
        name="test_agent",
        role="Test Role",
        goal="Test Goal",
        backstory="Test Backstory",
    )
    assert agent.name == "test_agent"
    assert str(agent) == "test_agent"


@pytest.mark.django_db
def test_list_agents_api(authed):
    client = authed
    Agent.objects.create(
        name="test_agent_1",
        role="Test Role 1",
        goal="Test Goal 1",
        backstory="Test Backstory 1",
    )
    Agent.objects.create(
        name="test_agent_2",
        role="Test Role 2",
        goal="Test Goal 2",
        backstory="Test Backstory 2",
    )
    url = reverse("agent-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_create_agent_api(authed):
    client = authed
    url = reverse("agent-list")
    data = {
        "name": "test_agent_3",
        "role": "Test Role 3",
        "goal": "Test Goal 3",
        "backstory": "Test Backstory 3",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Agent.objects.count() == 1
    agent = Agent.objects.first()
    assert agent.name == "test_agent_3"
