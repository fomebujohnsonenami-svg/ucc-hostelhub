from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from common.models import TimestampedModel


class RoommateProfile(TimestampedModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    student = models.OneToOneField("accounts.Profile", on_delete=models.CASCADE, related_name="roommate_profile", limit_choices_to={"role": "student"})
    display_name = models.CharField(max_length=100)
    preferred_area = models.CharField(max_length=100)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], help_text="GHS")
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], help_text="GHS")
    student_level = models.CharField(max_length=12)
    lifestyle_preferences = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    moderation_hidden = models.BooleanField(default=False, editable=False)
    visibility = models.CharField(max_length=10, choices=Visibility, default=Visibility.PRIVATE)

    class Meta:
        db_table = "roommate_profiles"
        indexes = [models.Index(fields=["visibility", "preferred_area", "student_level"], name="roommate_discovery_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(budget_min__gte=0, budget_max__gte=F("budget_min")), name="roommate_valid_budget"),
        ]
