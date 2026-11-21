from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.api import approved_hostels
from apps.hostels.models import Hostel
from apps.messaging.models import Message
from apps.roommates.api import visible_profiles
from apps.roommates.models import RoommateProfile
from common.api import AdminOnly, Page, object_data
from common.models import VerificationStatus

from .models import ModerationReport


class AccountSummary(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "full_name", "username", "role", "created_at")


class ReviewListing(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.business_name", read_only=True)

    class Meta:
        model = Hostel
        fields = ("id", "name", "area", "address", "description", "manager_name", "verification_status", "publication_status")


class ManagerReview(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = ManagerProfile
        fields = ("id", "full_name", "business_name", "verification_status", "verification_notes")


class ReportSerializer(serializers.ModelSerializer):
    reason = serializers.CharField(max_length=1500)

    class Meta:
        model = ModerationReport
        fields = ("id", "target_type", "target_id", "reason", "status", "created_at")
        read_only_fields = ("status", "created_at")


class ModerationList(generics.ListAPIView):
    permission_classes = [AdminOnly]
    pagination_class = Page


class Users(ModerationList):
    serializer_class = AccountSummary
    queryset = Profile.objects.order_by("-created_at", "pk")


class Listings(ModerationList):
    serializer_class = ReviewListing

    def get_queryset(self):
        queryset = Hostel.objects.select_related("manager").order_by("-updated_at", "pk")
        status = self.request.query_params.get("status")
        return queryset.filter(publication_status=status) if status else queryset


class ListingAction(generics.GenericAPIView):
    permission_classes = [AdminOnly]

    @transaction.atomic
    def post(self, request, pk):
        hostel = get_object_or_404(Hostel.objects.select_for_update(), pk=pk)
        action = object_data(request).get("action")
        if action in ("approve", "reject") and hostel.publication_status == Hostel.PublicationStatus.PENDING:
            hostel.verification_status = VerificationStatus.VERIFIED if action == "approve" else VerificationStatus.REJECTED
            hostel.publication_status = Hostel.PublicationStatus.DRAFT
        elif action == "suspend" and hostel.publication_status == Hostel.PublicationStatus.PUBLISHED:
            hostel.verification_status = VerificationStatus.REJECTED
            hostel.publication_status = Hostel.PublicationStatus.HIDDEN
            hostel.featured = False
        else:
            raise ValidationError({"action": "That review action is unavailable for this listing."})
        hostel.save(update_fields=["verification_status", "publication_status", "featured", "updated_at"])
        return Response(ReviewListing(hostel).data)


class Managers(ModerationList):
    serializer_class = ManagerReview
    queryset = ManagerProfile.objects.select_related("user").order_by("-created_at", "pk")


class VerifyManagerInput(serializers.Serializer):
    verification_status = serializers.ChoiceField(choices=VerificationStatus)
    verification_notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class VerifyManager(generics.GenericAPIView):
    permission_classes = [AdminOnly]
    serializer_class = VerifyManagerInput

    def patch(self, request, pk):
        manager = get_object_or_404(ManagerProfile, pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(manager, field, value)
        manager.save(update_fields=serializer.validated_data.keys())
        return Response(ManagerReview(manager).data)


class Reports(ModerationList):
    serializer_class = ReportSerializer
    queryset = ModerationReport.objects.order_by("-created_at", "pk")


class ReportAction(generics.GenericAPIView):
    permission_classes = [AdminOnly]

    @transaction.atomic
    def patch(self, request, pk):
        report = get_object_or_404(ModerationReport.objects.select_for_update(), pk=pk)
        action = object_data(request).get("action")
        if action == "remove":
            if report.target_type == ModerationReport.TargetType.HOSTEL:
                target = get_object_or_404(Hostel.objects.select_for_update(), pk=report.target_id)
                target.publication_status = Hostel.PublicationStatus.HIDDEN
                target.verification_status = VerificationStatus.REJECTED
                target.featured = False
                target.save(update_fields=["publication_status", "verification_status", "featured", "updated_at"])
            elif report.target_type == ModerationReport.TargetType.ROOMMATE:
                target = get_object_or_404(RoommateProfile.objects.select_for_update(), pk=report.target_id)
                target.moderation_hidden = True
                target.save(update_fields=["moderation_hidden", "updated_at"])
            elif report.target_type == ModerationReport.TargetType.MESSAGE:
                Message.objects.filter(pk=report.target_id).update(body="[Removed by moderation]", edited_at=timezone.now())
            else:
                raise ValidationError({"action": "This report does not support content removal."})
            report.status = ModerationReport.Status.RESOLVED
            report.save(update_fields=["status"])
            return Response(ReportSerializer(report).data)
        field = serializers.ChoiceField(choices=ModerationReport.Status)
        try:
            report.status = field.run_validation(object_data(request).get("status"))
        except ValidationError as error:
            raise ValidationError({"status": error.detail}) from error
        report.save(update_fields=["status"])
        return Response(ReportSerializer(report).data)


class ReportContent(generics.CreateAPIView):
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        visible = {
            "hostel": approved_hostels,
            "roommate": visible_profiles,
            "message": lambda: Message.objects.filter(conversation__participants=self.request.user),
            "profile": lambda: Profile.objects.filter(pk=self.request.user.pk),
        }
        get_object_or_404(visible[data["target_type"]](), pk=data["target_id"])
        serializer.save(reporter=self.request.user)
