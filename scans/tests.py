import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Scan, Finding
from .tasks import run_scan
from unittest.mock import patch

@pytest.mark.django_db
def test_scan_creation():
    scan = Scan.objects.create(provider="AWS")
    assert scan.provider == "AWS"
    assert scan.status == "pending"
    assert str(scan) == f"Scan {scan.id} for AWS (pending)"

@pytest.mark.django_db
def test_finding_creation():
    scan = Scan.objects.create(provider="AWS")
    finding = Finding.objects.create(
        scan=scan,
        check_name="test_check",
        resource_id="test_resource",
        status="fail",
        description="This is a test finding."
    )
    assert finding.scan == scan
    assert finding.check_name == "test_check"
    assert str(finding) == f"Finding for test_resource in scan {scan.id} (fail)"

@pytest.mark.django_db
def test_list_scans():
    client = APIClient()
    Scan.objects.create(provider="AWS")
    Scan.objects.create(provider="GCP")

    url = reverse("scan-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 2

@pytest.mark.django_db
@patch('scans.tasks.run_scan.delay')
def test_create_scan(mock_run_scan):
    client = APIClient()
    url = reverse("scan-list")
    data = {"provider": "AWS"}

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Scan.objects.count() == 1
    scan = Scan.objects.first()
    assert scan.provider == "AWS"
    mock_run_scan.assert_called_once_with(scan.id)

@pytest.mark.django_db
def test_list_findings():
    client = APIClient()
    scan = Scan.objects.create(provider="AWS")
    Finding.objects.create(scan=scan, check_name="check1", resource_id="res1", status="pass", description="")
    Finding.objects.create(scan=scan, check_name="check2", resource_id="res2", status="fail", description="")

    url = reverse("finding-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 2

@pytest.mark.django_db
@patch('scans.tasks.EEAuditor')
def test_run_scan_task_integration(MockEEAuditor):
    # Mock the EEAuditor instance and its methods
    mock_auditor_instance = MockEEAuditor.return_value
    mock_auditor_instance.run_aws_checks.return_value = [
        {
            "Title": "Test Check 1",
            "Resources": [{"Id": "resource1"}],
            "Compliance": {"Status": "FAILED"},
            "Description": "This is a test finding 1."
        },
        {
            "Title": "Test Check 2",
            "Resources": [{"Id": "resource2"}],
            "Compliance": {"Status": "PASSED"},
            "Description": "This is a test finding 2."
        }
    ]

    # Create a scan
    scan = Scan.objects.create(provider="AWS")

    # Run the task synchronously
    run_scan(scan.id)

    # Refresh the scan object from the database
    scan.refresh_from_db()

    # Assert that the scan is completed
    assert scan.status == "completed"

    # Assert that the findings were created
    assert Finding.objects.count() == 2

    # Check the details of the first finding
    finding1 = Finding.objects.get(check_name="Test Check 1")
    assert finding1.scan == scan
    assert finding1.resource_id == "resource1"
    assert finding1.status == "fail"
    assert finding1.description == "This is a test finding 1."

    # Check the details of the second finding
    finding2 = Finding.objects.get(check_name="Test Check 2")
    assert finding2.scan == scan
    assert finding2.resource_id == "resource2"
    assert finding2.status == "pass"
    assert finding2.description == "This is a test finding 2."
