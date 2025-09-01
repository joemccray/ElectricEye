from celery import shared_task

from eeauditor.eeauditor import EEAuditor

from .models import Finding, Scan


@shared_task
def run_scan(scan_id):
    """
    Celery task to run an ElectricEye scan.
    """
    scan = Scan.objects.get(id=scan_id)
    scan.status = "in_progress"
    scan.save()

    try:
        # Create an instance of the EEAuditor class.
        # We need to pass the correct arguments to the constructor.
        # For now, we'll use some default values.
        app = EEAuditor(assessmentTarget=scan.provider, args=None, useToml="False")

        # Load the plugins
        app.load_plugins()

        # Run the checks based on the provider
        if scan.provider == "AWS":
            findings_generator = app.run_aws_checks()
        elif scan.provider == "GCP":
            findings_generator = app.run_gcp_checks()
        elif scan.provider == "OCI":
            findings_generator = app.run_oci_checks()
        elif scan.provider == "Azure":
            findings_generator = app.run_azure_checks()
        elif scan.provider == "M365":
            findings_generator = app.run_m365_checks()
        elif scan.provider == "Salesforce":
            findings_generator = app.run_salesforce_checks()
        elif scan.provider == "Snowflake":
            findings_generator = app.run_snowflake_checks()
        else:
            findings_generator = app.run_non_aws_checks()

        # Process the findings
        for finding in findings_generator:
            # The finding is already a dictionary, no need to load from JSON
            Finding.objects.create(
                scan=scan,
                check_name=finding.get("Title", "N/A"),
                resource_id=finding.get("Resources", [{}])[0].get("Id", "N/A"),
                status=(
                    "fail"
                    if finding.get("Compliance", {}).get("Status") == "FAILED"
                    else "pass"
                ),
                description=finding.get("Description", ""),
            )

        scan.status = "completed"
        scan.save()

    except Exception as e:
        scan.status = "failed"
        scan.save()
        # In a real application, you'd want to log this exception
        print(f"Scan {scan.id} failed: {e}")
