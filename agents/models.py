from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=255)
    goal = models.TextField()
    backstory = models.TextField()
    is_qa_agent = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Task(models.Model):
    agent = models.ForeignKey(Agent, related_name="tasks", on_delete=models.CASCADE)
    description = models.TextField()
    expected_output = models.TextField()

    def __str__(self):
        return self.description


class Crew(models.Model):
    name = models.CharField(max_length=100, unique=True)
    agents = models.ManyToManyField(Agent, related_name="crews")
    tasks = models.ManyToManyField(Task, related_name="crews")

    def __str__(self):
        return self.name


class Job(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    crew = models.ForeignKey(Crew, related_name="jobs", on_delete=models.CASCADE)
    inputs = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} for crew {self.crew.name} ({self.status})"
