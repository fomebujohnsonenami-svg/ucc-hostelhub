from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from common.models import UUIDModel


class SubscriptionPlan(UUIDModel):
    class BillingPeriod(models.TextChoices):
        MONTH = "month", "Month"
        SEMESTER = "semester", "Semester"
        YEAR = "year", "Year"

    class Audience(models.TextChoices):
        STUDENT = "student", "Student"
        MANAGER = "manager", "Hostel manager"

    audience = models.CharField(max_length=12, choices=Audience, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], help_text="GHS")
    billing_period = models.CharField(max_length=12, choices=BillingPeriod)
    features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "subscription_plans"
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="subscription_nonnegative_price"),
            models.UniqueConstraint(fields=["name", "billing_period"], name="unique_subscription_plan_period"),
        ]


class ManagerSubscription(UUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        CANCELLED = "cancelled", "Cancelled"

    manager = models.ForeignKey("accounts.ManagerProfile", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=12, choices=Status, default=Status.PENDING)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "manager_subscriptions"
        indexes = [models.Index(fields=["manager", "status", "expires_at"], name="manager_subscription_idx")]
        constraints = [models.CheckConstraint(condition=Q(expires_at__gt=F("starts_at")), name="subscription_valid_dates")]
