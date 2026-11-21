from django.db import models

from common.models import UUIDModel


class ModerationReport(UUIDModel):
    class TargetType(models.TextChoices):
        PROFILE = "profile", "Profile"
        HOSTEL = "hostel", "Hostel"
        ROOMMATE = "roommate", "Roommate profile"
        MESSAGE = "message", "Message"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey("accounts.Profile", on_delete=models.SET_NULL, null=True, related_name="moderation_reports")
    target_type = models.CharField(max_length=12, choices=TargetType)
    target_id = models.UUIDField()
    reason = models.TextField()
    status = models.CharField(max_length=12, choices=Status, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "moderation_reports"
        indexes = [
            models.Index(fields=["status", "-created_at"], name="moderation_queue_idx"),
            models.Index(fields=["target_type", "target_id"], name="moderation_target_idx"),
        ]
