import logging
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.accounts.models import Profile
from apps.hostels.models import Hostel, HostelImage

from .models import VerificationStatus
from .storage import IMAGE_TYPE, StorageUnavailable, delete_image, fetch_image, normalize_image, put_image

logger = logging.getLogger(__name__)


def can_manage(user, hostel):
    return user.role == Profile.Role.ADMIN or (
        user.role == Profile.Role.MANAGER and hostel.manager.user_id == user.pk
    )


def require_manager(user, hostel):
    if user.role != Profile.Role.MANAGER or hostel.manager.user_id != user.pk:
        raise PermissionDenied()


def cleanup_image(bucket, path):
    try:
        delete_image(bucket, path)
    except StorageUnavailable:
        logger.warning("Could not remove unreferenced image %s in bucket %s", path, bucket)


def image_response(bucket, path):
    response = HttpResponse(fetch_image(bucket, path), content_type=IMAGE_TYPE)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def hostel_listing(hostel_id, *, for_update=False):
    queryset = Hostel.objects.select_related("manager")
    if for_update:
        queryset = queryset.select_for_update()
    return get_object_or_404(queryset, pk=hostel_id)


@api_view(["POST"])
@parser_classes([MultiPartParser])
def hostel_image_upload(request, hostel_id):
    require_manager(request.user, hostel_listing(hostel_id))
    content = normalize_image(request.FILES.get("image"))
    bucket = settings.SUPABASE_HOSTEL_BUCKET
    image_id = uuid4()
    path = f"{hostel_id}/{image_id}.webp"
    stored = False
    try:
        with transaction.atomic():
            hostel = hostel_listing(hostel_id, for_update=True)
            require_manager(request.user, hostel)
            if hostel.images.count() >= 12:
                raise ValidationError({"image": "A hostel may have up to 12 images."})
            last = hostel.images.aggregate(last=Max("sort_order"))["last"]
            put_image(bucket, path, content)
            stored = True
            image = HostelImage.objects.create(
                id=image_id, hostel=hostel, storage_path=path, sort_order=0 if last is None else last + 1,
            )
    except Exception:
        if stored:
            cleanup_image(bucket, path)
        raise
    return Response({"id": str(image.pk), "sort_order": image.sort_order}, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
def hostel_image_detail(request, hostel_id, image_id):
    bucket = settings.SUPABASE_HOSTEL_BUCKET
    if request.method == "GET":
        hostel = hostel_listing(hostel_id)
        public = (hostel.publication_status == Hostel.PublicationStatus.PUBLISHED
                  and hostel.verification_status == VerificationStatus.VERIFIED)
        if not public and not can_manage(request.user, hostel):
            raise PermissionDenied()
        image = get_object_or_404(hostel.images, pk=image_id)
        return image_response(bucket, image.storage_path)

    with transaction.atomic():
        hostel = hostel_listing(hostel_id, for_update=True)
        require_manager(request.user, hostel)
        image = get_object_or_404(hostel.images, pk=image_id)
        delete_image(bucket, image.storage_path)
        image.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "PUT", "DELETE"])
@parser_classes([MultiPartParser])
def avatar(request):
    bucket = settings.SUPABASE_AVATAR_BUCKET
    if request.method == "GET":
        if not request.user.avatar_storage_path:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return image_response(bucket, request.user.avatar_storage_path)

    if request.method == "DELETE":
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(pk=request.user.pk)
            if profile.avatar_storage_path:
                delete_image(bucket, profile.avatar_storage_path)
                profile.avatar_storage_path = ""
                profile.save(update_fields=["avatar_storage_path", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    content = normalize_image(request.FILES.get("image"))
    path = f"{request.user.pk}/{uuid4()}.webp"
    stored = False
    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(pk=request.user.pk)
            previous = profile.avatar_storage_path
            put_image(bucket, path, content)
            stored = True
            profile.avatar_storage_path = path
            profile.save(update_fields=["avatar_storage_path", "updated_at"])
            if previous:
                transaction.on_commit(lambda: cleanup_image(bucket, previous))
    except Exception:
        if stored:
            cleanup_image(bucket, path)
        raise
    return Response(status=status.HTTP_204_NO_CONTENT)
