from io import BytesIO
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Hostel, HostelImage
from common.storage import MAX_IMAGE_BYTES, StorageUnavailable, delete_image, fetch_image


def sample_image():
    content = BytesIO()
    Image.new("RGB", (12, 12), "purple").save(content, "PNG")
    return SimpleUploadedFile("sample.png", content.getvalue(), content_type="image/png")


class ImageApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Profile.objects.create(id=uuid4(), full_name="Manager", username="manager", role=Profile.Role.MANAGER)
        cls.other = Profile.objects.create(id=uuid4(), full_name="Other Manager", username="other", role=Profile.Role.MANAGER)
        cls.student = Profile.objects.create(id=uuid4(), full_name="Student", username="student")
        cls.admin = Profile.objects.create(id=uuid4(), full_name="Admin", username="admin", role=Profile.Role.ADMIN)
        manager = ManagerProfile.objects.create(user=cls.owner, business_name="Test")
        cls.hostel = Hostel.objects.create(manager=manager, name="Test Hostel")
        cls.upload = reverse("hostel-image-upload", args=[cls.hostel.pk])
        cls.avatar = reverse("profile-avatar")

    @patch("common.image_views.put_image")
    def test_guest_and_nonowner_cannot_upload(self, put):
        client = APIClient()
        self.assertEqual(client.post(self.upload, {"image": sample_image()}, format="multipart").status_code, 401)
        for profile in (self.other, self.student):
            client.force_authenticate(profile)
            self.assertEqual(client.post(self.upload, {"image": sample_image()}, format="multipart").status_code, 403)
        put.assert_not_called()

    @patch("common.image_views.fetch_image", return_value=b"mock webp")
    @patch("common.image_views.delete_image")
    @patch("common.image_views.put_image")
    def test_hostel_image_lifecycle(self, put, delete, fetch):
        client = APIClient()
        client.force_authenticate(self.owner)
        response = client.post(self.upload, {"image": sample_image()}, format="multipart")
        self.assertEqual(response.status_code, 201)
        image = HostelImage.objects.get(pk=response.json()["id"])
        self.assertNotIn("storage_path", response.json())
        bucket, path, content = put.call_args.args
        self.assertEqual(path, f"{self.hostel.pk}/{image.pk}.webp")
        self.assertEqual(Image.open(BytesIO(content)).format, "WEBP")
        detail = reverse("hostel-image-detail", args=[self.hostel.pk, image.pk])
        client.force_authenticate(self.student)
        self.assertEqual(client.get(detail).status_code, 403)
        self.assertEqual(client.delete(detail).status_code, 403)
        self.hostel.publication_status = Hostel.PublicationStatus.PUBLISHED
        self.hostel.verification_status = "verified"
        self.hostel.save()
        response = client.get(detail)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        fetch.assert_called_once_with(bucket, path)
        client.force_authenticate(self.admin)
        self.assertEqual(client.delete(detail).status_code, 403)
        client.force_authenticate(self.owner)
        self.assertEqual(client.delete(detail).status_code, 204)
        delete.assert_called_once_with(bucket, path)
        self.assertFalse(HostelImage.objects.filter(pk=image.pk).exists())

    @patch("common.image_views.put_image", side_effect=StorageUnavailable)
    def test_invalid_file_never_reaches_storage_and_failure_does_not_create_row(self, put):
        client = APIClient()
        client.force_authenticate(self.owner)
        response = client.post(self.upload, {"image": SimpleUploadedFile("fake.jpg", b"<svg/>", "image/jpeg")}, format="multipart")
        self.assertEqual(response.status_code, 400)
        put.assert_not_called()
        self.assertEqual(client.post(self.upload, {"image": sample_image()}, format="multipart").status_code, 503)
        self.assertFalse(HostelImage.objects.exists())

    @patch("common.image_views.delete_image")
    @patch("common.image_views.put_image")
    def test_avatar_replacement_and_removal(self, put, delete):
        client = APIClient()
        client.force_authenticate(self.student)
        self.assertEqual(client.get(self.avatar).status_code, 404)
        self.assertEqual(client.put(self.avatar, {"image": sample_image()}, format="multipart").status_code, 204)
        self.student.refresh_from_db()
        original_path = self.student.avatar_storage_path
        self.assertTrue(original_path.startswith(f"{self.student.pk}/"))
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(client.put(self.avatar, {"image": sample_image()}, format="multipart").status_code, 204)
        self.student.refresh_from_db()
        self.assertNotEqual(original_path, self.student.avatar_storage_path)
        delete.assert_called_once_with(put.call_args.args[0], original_path)
        self.assertEqual(client.delete(self.avatar).status_code, 204)
        self.student.refresh_from_db()
        self.assertEqual(self.student.avatar_storage_path, "")


@override_settings(SUPABASE_URL="https://project.example.com", SUPABASE_SERVICE_ROLE_KEY="sample-service-key")
class StorageContractTests(SimpleTestCase):
    @patch("common.storage.httpx.request")
    def test_private_requests_use_server_key_and_documented_routes(self, request):
        request.return_value = httpx.Response(200, content=b"mock")
        self.assertEqual(fetch_image("avatars", "a/b.webp"), b"mock")
        self.assertEqual(request.call_args.args, ("GET", "https://project.example.com/storage/v1/object/authenticated/avatars/a/b.webp"))
        self.assertEqual(request.call_args.kwargs["headers"]["apikey"], "sample-service-key")
        delete_image("avatars", "a/b.webp")
        self.assertEqual(request.call_args.kwargs["json"], {"prefixes": ["a/b.webp"]})

    @patch("common.management.commands.configure_storage.restrict_direct_storage_access")
    @patch("common.management.commands.configure_storage.storage_request")
    def test_bucket_command_creates_and_updates_private_buckets(self, request, restrict):
        request.side_effect = [Mock(status_code=404), Mock(), Mock(status_code=200), Mock()]
        call_command("configure_storage", stdout=Mock())
        restrict.assert_called_once_with(("hostel-images", "avatars"))
        calls = request.call_args_list
        limits = {"public": False, "file_size_limit": MAX_IMAGE_BYTES, "allowed_mime_types": ["image/webp"]}
        self.assertEqual(calls[1].kwargs["json"], {"id": "hostel-images", "name": "hostel-images", **limits})
        self.assertEqual(calls[3].kwargs["json"], limits)
