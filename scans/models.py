from django.db import models

class Scan(models.Model):
    """
    Represents a single audit scan.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    provider = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Scan {self.id} for {self.provider} ({self.status})"

class Finding(models.Model):
    """
    Represents a single finding from a scan.
    """
    STATUS_CHOICES = [
        ("pass", "Pass"),
        ("fail", "Fail"),
    ]

    scan = models.ForeignKey(Scan, related_name="findings", on_delete=models.CASCADE)
    check_name = models.CharField(max_length=255)
    resource_id = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Finding for {self.resource_id} in scan {self.scan.id} ({self.status})"
