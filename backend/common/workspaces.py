from django.db.models import Sum
from rest_framework import generics, serializers
from rest_framework.response import Response

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.api import PublicHostelSerializer, published_hostels, listing_data
from apps.hostels.models import Hostel, RoomType
from apps.messaging.models import Conversation
from apps.moderation.models import ModerationReport
from common.api import AdminOnly, ManagerOnly, StudentOnly


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "full_name", "username", "role", "phone")
        read_only_fields = ("id", "role")


class Me(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class StudentDashboard(generics.GenericAPIView):
    permission_classes = [StudentOnly]

    def get(self, request):
        hostels = published_hostels()
        return Response({
            "saved": hostels.filter(saves__student=request.user).count(),
            "conversations": Conversation.objects.filter(participants=request.user).count(),
            "recommended": PublicHostelSerializer(listing_data(hostels).order_by("-updated_at", "pk")[:3], many=True).data,
        })


class ManagerDashboard(generics.GenericAPIView):
    permission_classes = [ManagerOnly]

    def get(self, request):
        hostels = Hostel.objects.filter(manager__user=request.user)
        counts = RoomType.objects.filter(hostel__in=hostels).aggregate(rooms=Sum("total_rooms", default=0), beds=Sum("available_beds", default=0))
        return Response({
            "hostels": hostels.count(), **counts,
            "inquiries": Conversation.objects.filter(participants=request.user, conversation_type=Conversation.Type.HOSTEL).count(),
        })


class AdminDashboard(generics.GenericAPIView):
    permission_classes = [AdminOnly]

    def get(self, request):
        return Response({
            "users": Profile.objects.count(),
            "listings": published_hostels().count(),
            "verification": ManagerProfile.objects.filter(verification_status="pending").count(),
            "moderation": ModerationReport.objects.filter(status__in=("open", "reviewing")).count(),
        })
