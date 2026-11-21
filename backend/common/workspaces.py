import jwt
from django.db import IntegrityError, transaction
from django.db.models import Sum
from rest_framework import generics, permissions, serializers
from rest_framework.authentication import get_authorization_header
from rest_framework.response import Response

from apps.accounts.authentication import access_token_subject
from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.api import PublicHostelSerializer, approved_hostels, listing_data
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
        hostels = approved_hostels()
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
            "listings": Hostel.objects.filter(publication_status=Hostel.PublicationStatus.PENDING).count(),
            "verification": ManagerProfile.objects.filter(verification_status="pending").count(),
            "moderation": ModerationReport.objects.filter(status__in=("open", "reviewing")).count(),
        })


class OnboardingSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    username = serializers.SlugField(max_length=64)
    role = serializers.ChoiceField(choices=("student", "manager"))
    business_name = serializers.CharField(max_length=160, required=False)

    def validate(self, attrs):
        if attrs["role"] == Profile.Role.MANAGER and not attrs.get("business_name"):
            raise serializers.ValidationError({"business_name": "Enter your business name."})
        return attrs


class Onboarding(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = OnboardingSerializer

    def post(self, request):
        header = get_authorization_header(request).split()
        if len(header) != 2 or header[0].lower() != b"bearer":
            return Response({"detail": "A Supabase access token is required."}, status=401)
        try:
            user_id = access_token_subject(header[1])
        except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
            return Response({"detail": "Invalid or expired access token."}, status=401)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data.copy()
        business = fields.pop("business_name", None)
        try:
            with transaction.atomic():
                profile, created = Profile.objects.get_or_create(pk=user_id, defaults=fields)
                if created and profile.role == Profile.Role.MANAGER:
                    ManagerProfile.objects.create(user=profile, business_name=business)
        except IntegrityError:
            raise serializers.ValidationError({"username": "Choose a different username."}) from None
        return Response(MeSerializer(profile).data, status=201 if created else 200)
