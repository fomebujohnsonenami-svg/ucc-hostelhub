from io import BytesIO
from urllib.parse import quote

import httpx
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import APIException, ValidationError

from common.supabase_config import project_url

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
IMAGE_TYPE = "image/webp"


class StorageUnavailable(APIException):
    status_code = 503
    default_detail = "Image storage is unavailable. Please try again later."


def normalize_image(upload):
    if upload is None:
        raise ValidationError({"image": "Upload an image file."})
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError({"image": "Images must be 5 MiB or smaller."})
    try:
        with Image.open(upload, formats=["JPEG", "PNG", "WEBP"]) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS or getattr(source, "is_animated", False):
                raise ValidationError({"image": "Use a still image up to 16 megapixels."})
            image = ImageOps.exif_transpose(source).convert("RGBA")
            image.thumbnail((1800, 1800))
            output = BytesIO()
            image.save(output, "WEBP", quality=85)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValidationError({"image": "Use a valid JPEG, PNG or WebP image."}) from None
    if output.tell() > MAX_IMAGE_BYTES:
        raise ValidationError({"image": "The processed image exceeds 5 MiB."})
    return output.getvalue()


def storage_request(method, endpoint, *, allowed=(200, 201), **kwargs):
    try:
        url = project_url()
    except ValueError:
        raise StorageUnavailable() from None
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key:
        raise StorageUnavailable()
    extra_headers = kwargs.pop("headers", {})
    try:
        response = httpx.request(
            method, f"{url}/storage/v1/{endpoint}", timeout=15.0,
            headers={"apikey": key, "Authorization": f"Bearer {key}", **extra_headers},
            **kwargs,
        )
    except httpx.HTTPError:
        raise StorageUnavailable() from None
    if response.status_code not in allowed:
        raise StorageUnavailable()
    return response


def object_endpoint(bucket, path):
    return f"object/{quote(bucket, safe='')}/{quote(path, safe='/')}"


def put_image(bucket, path, content):
    storage_request("POST", object_endpoint(bucket, path), content=content, headers={"Content-Type": IMAGE_TYPE, "x-upsert": "false"})


def delete_image(bucket, path):
    storage_request("DELETE", f"object/{quote(bucket, safe='')}", json={"prefixes": [path]}, allowed=(200, 204))


def fetch_image(bucket, path):
    endpoint = object_endpoint(bucket, path).removeprefix("object/")
    return storage_request("GET", f"object/authenticated/{endpoint}").content
