from django.db import models
from django.db.models import Q

from common.models import TimestampedModel, UUIDModel, VerificationStatus


class Profile(TimestampedModel):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Administrator"

    # Provisioning must supply the UUID from a verified Supabase Auth token.
    id = models.UUIDField(primary_key=True, editable=False)
    full_name = models.CharField(max_length=150)
    username = models.SlugField(max_length=64, unique=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    avatar_storage_path = models.CharField(max_length=300, blank=True, editable=False)
    role = models.CharField(max_length=12, choices=Role, default=Role.STUDENT, db_index=True)
    phone = models.CharField(max_length=32, blank=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = "profiles"
        constraints = [
            models.CheckConstraint(condition=Q(role__in=["student", "manager", "admin"]), name="profile_valid_role"),
        ]


class ManagerProfile(UUIDModel):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="manager_profile", limit_choices_to={"role": Profile.Role.MANAGER})
    business_name = models.CharField(max_length=160)
    contact_phone = models.CharField(max_length=32, blank=True)
    verification_status = models.CharField(max_length=12, choices=VerificationStatus, default=VerificationStatus.PENDING, db_index=True)
    verification_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "manager_profiles"
