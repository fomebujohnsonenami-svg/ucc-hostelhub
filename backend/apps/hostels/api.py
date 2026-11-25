from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import ManagerProfile, Profile
from common.api import Page, StudentOnly, object_data
from common.image_views import cleanup_image, image_response
from common.models import VerificationStatus

from .models import Amenity, Hostel, RoomType, SavedHostel
from .operations import availability_stale, filter_hostels


def published_hostels():
    return Hostel.objects.filter(
        publication_status=Hostel.PublicationStatus.PUBLISHED,
    ).exclude(verification_status=VerificationStatus.REJECTED)


def listing_data(queryset):
    return queryset.prefetch_related(
        "amenities", "images",
        Prefetch("room_types", queryset=RoomType.objects.order_by("price_per_bed", "pk")),
    )


class RoomSerializer(serializers.ModelSerializer):
    availability_stale = serializers.SerializerMethodField()
    total_capacity = serializers.SerializerMethodField()

    def get_availability_stale(self, room):
        return availability_stale(room)

    def get_total_capacity(self, room):
        return room.capacity * room.total_rooms

    def validate(self, attrs):
        values = {key: attrs.get(key, getattr(self.instance, key, default)) for key, default in (
            ("capacity", 1), ("total_rooms", 0), ("available_beds", 0),
        )}
        if values["available_beds"] > values["capacity"] * values["total_rooms"]:
            raise ValidationError({"available_beds": "Available beds cannot exceed total capacity."})
        return attrs

    def update(self, instance, validated_data):
        # An explicit bed count reconfirms availability even when the count is unchanged.
        if "available_beds" in validated_data:
            validated_data["availability_updated_at"] = timezone.now()
        return super().update(instance, validated_data)

    class Meta:
        model = RoomType
        fields = (
            "id", "name", "price_per_bed", "billing_period", "total_rooms", "available_beds",
            "capacity", "total_capacity", "availability_updated_at", "availability_stale",
        )
        read_only_fields = ("availability_updated_at",)


class PublicHostelSerializer(serializers.ModelSerializer):
    amenities = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    room_types = RoomSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()

    def get_images(self, hostel):
        return [f"hostels/{hostel.pk}/photos/{image.pk}/" for image in hostel.images.all()]

    class Meta:
        model = Hostel
        fields = (
            "id", "name", "description", "address", "area", "latitude", "longitude",
            "amenities", "room_types", "images", "updated_at", "featured",
        )


class PublicHostels(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicHostelSerializer
    pagination_class = Page

    def get_queryset(self):
        queryset = published_hostels()
        if self.request.query_params.get("featured") == "yes":
            queryset = queryset.filter(featured=True)
        return listing_data(filter_hostels(queryset, self.request.query_params))


class PublicHostel(generics.RetrieveAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicHostelSerializer

    def get_queryset(self):
        return listing_data(published_hostels())


@api_view(["GET"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
def public_photo(request, pk, image_id):
    hostel = get_object_or_404(published_hostels(), pk=pk)
    image = get_object_or_404(hostel.images, pk=image_id)
    return image_response(settings.SUPABASE_HOSTEL_BUCKET, image.storage_path)


class ManagerHostelSerializer(serializers.ModelSerializer):
    amenities = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Amenity.objects.all(), required=False,
    )

    room_types = RoomSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()

    def get_images(self, hostel):
        return [str(image.pk) for image in hostel.images.all()]

    def validate(self, attrs):
        instance = self.instance
        latitude = attrs.get("latitude", instance.latitude if instance else None)
        longitude = attrs.get("longitude", instance.longitude if instance else None)
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Provide both coordinates or clear both.")
        return attrs

    class Meta:
        model = Hostel
        fields = (
            "id", "name", "description", "address", "area", "latitude", "longitude",
            "amenities", "publication_status", "verification_status", "room_types", "images", "updated_at",
        )
        read_only_fields = ("id", "publication_status", "verification_status", "updated_at")


class OwnerAccess:
    serializer_class = ManagerHostelSerializer

    def get_manager(self):
        user = self.request.user
        if user.role != Profile.Role.MANAGER:
            raise PermissionDenied("A manager profile is required.")
        manager = ManagerProfile.objects.filter(user=user).first()
        if manager is None:
            raise PermissionDenied("A manager profile is required.")
        return manager

    def get_queryset(self):
        return listing_data(Hostel.objects.filter(manager=self.get_manager())).order_by("-updated_at", "pk")


class ManagerHostels(OwnerAccess, generics.ListCreateAPIView):
    pagination_class = Page

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(manager=self.get_manager(), publication_status=Hostel.PublicationStatus.PUBLISHED)


class ManagerHostel(OwnerAccess, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete", "head", "options"]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def perform_destroy(self, hostel):
        if object_data(self.request).get("confirm") is not True:
            raise ValidationError({"confirm": "Explicit deletion confirmation is required."})
        paths = list(hostel.images.values_list("storage_path", flat=True))
        hostel.delete()
        for path in paths:
            transaction.on_commit(lambda path=path: cleanup_image(settings.SUPABASE_HOSTEL_BUCKET, path))

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_for_update() if self.request.method in {"PATCH", "DELETE"} else queryset


class Publication(OwnerAccess, generics.GenericAPIView):
    @transaction.atomic
    def post(self, request, pk):
        hostel = get_object_or_404(self.get_queryset().select_for_update(), pk=pk)
        action = object_data(request).get("action")
        if (
            action == "publish"
            and hostel.publication_status in {Hostel.PublicationStatus.DRAFT, Hostel.PublicationStatus.PENDING}
            and hostel.verification_status != VerificationStatus.REJECTED
        ):
            hostel.publication_status = Hostel.PublicationStatus.PUBLISHED
        elif action == "unpublish" and hostel.publication_status == Hostel.PublicationStatus.PUBLISHED:
            hostel.publication_status = Hostel.PublicationStatus.DRAFT
        else:
            raise ValidationError({"action": "This listing cannot make that publication change."})
        hostel.save(update_fields=["publication_status", "updated_at"])
        return Response(self.get_serializer(hostel).data)


class OwnerRooms(OwnerAccess):
    serializer_class = RoomSerializer

    def owned_hostel(self):
        return get_object_or_404(Hostel.objects.filter(manager=self.get_manager()).select_for_update(), pk=self.kwargs["hostel_id"])


class ManagerRooms(OwnerRooms, generics.GenericAPIView):
    @transaction.atomic
    def post(self, request, hostel_id):
        hostel = self.owned_hostel()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(hostel=hostel)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ManagerRoom(OwnerRooms, generics.GenericAPIView):
    @transaction.atomic
    def patch(self, request, hostel_id, pk):
        room = get_object_or_404(self.owned_hostel().room_types, pk=pk)
        serializer = self.get_serializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    def delete(self, request, hostel_id, pk):
        room = get_object_or_404(self.owned_hostel().room_types, pk=pk)
        if object_data(request).get("confirm") is not True:
            raise ValidationError({"confirm": "Explicit deletion confirmation is required."})
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Amenities(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(list(Amenity.objects.order_by("name").values_list("name", flat=True)))


class SavedListings(generics.ListAPIView):
    serializer_class = PublicHostelSerializer
    permission_classes = [StudentOnly]
    pagination_class = Page

    def get_queryset(self):
        return listing_data(published_hostels().filter(saves__student=self.request.user)).order_by("-saves__created_at", "pk")


class SavedListing(generics.GenericAPIView):
    permission_classes = [StudentOnly]

    def get(self, request, pk):
        return Response({"saved": SavedHostel.objects.filter(student=request.user, hostel_id=pk).exists()})

    def put(self, request, pk):
        hostel = get_object_or_404(published_hostels(), pk=pk)
        SavedHostel.objects.get_or_create(student=request.user, hostel=hostel)
        return Response({"saved": True})

    def delete(self, request, pk):
        SavedHostel.objects.filter(student=request.user, hostel_id=pk).delete()
        return Response({"saved": False})


class SavedIds(generics.GenericAPIView):
    permission_classes = [StudentOnly]

    def get(self, request):
        return Response(list(SavedHostel.objects.filter(student=request.user, hostel__in=published_hostels()).values_list("hostel_id", flat=True)))


class DiscoveryOptions(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        published = published_hostels()
        return Response({
            "areas": list(published.order_by("area").values_list("area", flat=True).distinct()),
            "room_types": list(RoomType.objects.filter(hostel__in=published).order_by("name").values_list("name", flat=True).distinct()),
        })
