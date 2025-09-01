from django.db import models
from django.conf import settings


class StripeCustomer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.user.username


class Subscription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("past_due", "Past Due"),
        ("unpaid", "Unpaid"),
    ]
    TIER_CHOICES = [
        ("free", "Free"),
        ("tier1", "$9/month"),
        ("tier2", "$19/month"),
        ("tier3", "$39/month"),
    ]
    customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.tier} ({self.status})"
