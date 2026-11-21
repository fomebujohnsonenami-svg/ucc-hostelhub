from django.db import models
from django.db.models import Q

from common.models import TimestampedModel, UUIDModel


class Conversation(TimestampedModel):
    class Type(models.TextChoices):
        HOSTEL = "hostel", "Hostel inquiry"
        ROOMMATE = "roommate", "Roommate inquiry"

    conversation_type = models.CharField(max_length=12, choices=Type, db_index=True)
    hostel = models.ForeignKey("hostels.Hostel", on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    participants = models.ManyToManyField("accounts.Profile", through="ConversationParticipant", related_name="conversations")

    class Meta:
        db_table = "conversations"
        indexes = [models.Index(fields=["-updated_at"], name="conversation_recent_idx")]
        constraints = [models.CheckConstraint(condition=Q(conversation_type="hostel") | Q(conversation_type="roommate", hostel__isnull=True), name="conversation_valid_type")]


class ConversationParticipant(UUIDModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE, related_name="conversation_memberships")
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversation_participants"
        constraints = [models.UniqueConstraint(fields=["conversation", "user"], name="unique_conversation_member")]


class Message(UUIDModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("accounts.Profile", on_delete=models.PROTECT, related_name="sent_messages")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "messages"
        indexes = [models.Index(fields=["conversation", "-created_at", "-id"], name="message_thread_order_idx")]
        constraints = [models.CheckConstraint(condition=~Q(body=""), name="message_nonempty_body")]
