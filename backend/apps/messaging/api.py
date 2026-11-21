from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.response import Response

from apps.accounts.models import Profile
from apps.hostels.api import approved_hostels
from apps.roommates.api import visible_profiles
from apps.subscriptions.access import messaging_access
from common.api import Page, object_data

from .models import Conversation, ConversationParticipant, Message


def memberships_for(user):
    return ConversationParticipant.objects.filter(user=user)


def conversation_list(user):
    return Conversation.objects.filter(memberships__user=user).annotate(
        unread=Count("messages", filter=~Q(messages__sender=user) & (
            Q(memberships__last_read_at__isnull=True) | Q(messages__created_at__gt=F("memberships__last_read_at"))
        )),
    ).select_related("hostel").prefetch_related(
        Prefetch("participants", queryset=Profile.objects.only("id", "full_name")),
    ).order_by("-updated_at", "pk")


class ConversationSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    unread = serializers.IntegerField(read_only=True)

    def get_name(self, conversation):
        user = self.context["request"].user
        if user.role == Profile.Role.STUDENT and conversation.hostel:
            return conversation.hostel.name
        return next((profile.full_name for profile in conversation.participants.all() if profile.pk != user.pk), "Conversation")

    class Meta:
        model = Conversation
        fields = ("id", "conversation_type", "name", "unread", "updated_at")


class ConversationInput(serializers.Serializer):
    hostel = serializers.UUIDField(required=False)
    roommate = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if len(attrs) != 1:
            raise serializers.ValidationError("Select exactly one hostel or roommate profile.")
        return attrs


class Conversations(generics.ListAPIView):
    serializer_class = ConversationSerializer
    pagination_class = Page

    def get_queryset(self):
        messaging_access(self.request.user)
        return conversation_list(self.request.user)

    @transaction.atomic
    def post(self, request):
        messaging_access(request.user, starts_conversation=True)
        serializer = ConversationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        hostel = None
        if "hostel" in data:
            hostel = get_object_or_404(approved_hostels().select_related("manager"), pk=data["hostel"])
            peer = hostel.manager.user_id
            kind = Conversation.Type.HOSTEL
        else:
            roommate = get_object_or_404(visible_profiles(), pk=data["roommate"])
            peer = roommate.student_id
            kind = Conversation.Type.ROOMMATE
        if peer == request.user.pk:
            raise serializers.ValidationError("You cannot start a conversation with yourself.")

        # Lock the pair in a stable order so concurrent requests reuse the same thread.
        list(Profile.objects.filter(pk__in=(peer, request.user.pk)).order_by("pk").select_for_update().values_list("pk", flat=True))
        existing = Conversation.objects.filter(conversation_type=kind, hostel=hostel, participants=request.user).filter(participants=peer).order_by("created_at").first()
        if existing:
            return Response({"id": str(existing.pk)})
        thread = Conversation.objects.create(conversation_type=kind, hostel=hostel)
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=thread, user_id=user_id) for user_id in (request.user.pk, peer)
        ])
        return Response({"id": str(thread.pk)}, status=201)


class MessageSerializer(serializers.ModelSerializer):
    body = serializers.CharField(max_length=2000)
    sent = serializers.SerializerMethodField()

    def get_sent(self, message):
        return message.sender_id == self.context["request"].user.pk

    class Meta:
        model = Message
        fields = ("id", "body", "created_at", "sent")
        read_only_fields = ("created_at",)


class ThreadAccess:
    def membership(self):
        messaging_access(self.request.user)
        return get_object_or_404(memberships_for(self.request.user), conversation_id=self.kwargs["pk"])


class Messages(ThreadAccess, generics.ListCreateAPIView):
    pagination_class = Page
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(conversation_id=self.membership().conversation_id).order_by("-created_at", "-pk")

    @transaction.atomic
    def perform_create(self, serializer):
        membership = self.membership()
        thread = Conversation.objects.select_for_update().get(pk=membership.conversation_id)
        serializer.save(conversation=thread, sender=self.request.user)
        Conversation.objects.filter(pk=thread.pk).update(updated_at=timezone.now())


class ReadMessages(ThreadAccess, generics.GenericAPIView):
    def post(self, request, pk):
        membership = self.membership()
        field = serializers.UUIDField()
        message_id = field.run_validation(object_data(request).get("message"))
        message = get_object_or_404(Message.objects.filter(conversation_id=membership.conversation_id), pk=message_id)
        ConversationParticipant.objects.filter(pk=membership.pk).filter(
            Q(last_read_at__isnull=True) | Q(last_read_at__lt=message.created_at)
        ).update(last_read_at=message.created_at)
        return Response(status=204)


class ConversationDetail(ThreadAccess, generics.RetrieveAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        self.membership()
        return conversation_list(self.request.user)
