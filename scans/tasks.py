from celery import shared_task

from .services import run_scan_service


@shared_task(ignore_result=True)
def run_scan(scan_id):
    """
    Celery task to run an ElectricEye scan.
    """
    run_scan_service(scan_id)
