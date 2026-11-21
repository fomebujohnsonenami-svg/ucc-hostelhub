from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Hostel, HostelImage, RoomType
from common.models import VerificationStatus


class HostelLocationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Profile.objects.create(id=uuid4(), role="manager", username="owner")
        cls.other = Profile.objects.create(id=uuid4(), role="manager", username="other")
        cls.student = Profile.objects.create(id=uuid4(), role="student", username="student")
        cls.admin = Profile.objects.create(id=uuid4(), role="admin", username="admin")
        cls.manager = ManagerProfile.objects.create(user=cls.owner, business_name="Owner")
        ManagerProfile.objects.create(user=cls.other, business_name="Other")
        cls.approved = Hostel.objects.create(
            manager=cls.manager, name="Approved fixture", address="Fixture address", area="Amamoma",
            latitude=Decimal("5.125001"), longitude=Decimal("-1.296002"),
            publication_status="published", verification_status=VerificationStatus.VERIFIED,
        )
        cls.unlocated = Hostel.objects.create(
            manager=cls.manager, name="Unlocated fixture",
            publication_status="published", verification_status=VerificationStatus.VERIFIED,
        )
        cls.unverified = Hostel.objects.create(manager=cls.manager, name="Unverified", publication_status="published")
        cls.pending = Hostel.objects.create(
            manager=cls.manager, name="Pending", publication_status="pending",
            verification_status=VerificationStatus.VERIFIED,
        )
        cls.cover = HostelImage.objects.create(hostel=cls.approved, storage_path="approved/cover.webp")
        cls.private_cover = HostelImage.objects.create(hostel=cls.pending, storage_path="pending/cover.webp")
        RoomType.objects.create(hostel=cls.approved, name="Double", capacity=2, total_rooms=2, available_beds=3, price_per_bed=900)

    def setUp(self):
        self.client = APIClient()
        self.manager_hostels = reverse("manager-hostels")
        self.detail = reverse("manager-hostel", args=[self.approved.pk])

    def test_public_api_returns_only_approved_listings_with_exact_values(self):
        response = self.client.get(reverse("public-hostels"))
        self.assertEqual(response.status_code, 200)
        listings = {item["id"]: item for item in response.json()["results"]}
        self.assertEqual(set(listings), {str(self.approved.pk), str(self.unlocated.pk)})
        located = listings[str(self.approved.pk)]
        self.assertEqual((located["latitude"], located["longitude"]), ("5.125001", "-1.296002"))
        self.assertEqual(located["room_types"][0]["available_beds"], 3)
        self.assertIn(str(self.cover.pk), located["images"][0])
        self.assertIsNone(listings[str(self.unlocated.pk)]["latitude"])
        self.assertEqual(self.client.get(reverse("public-hostel", args=[self.pending.pk])).status_code, 404)

    @patch("common.image_views.fetch_image", return_value=b"test cover")
    def test_public_photo_respects_approval_and_hostel_membership(self, fetch):
        self.assertEqual(self.client.get(reverse("public-hostel-photo", args=[self.approved.pk, self.cover.pk])).content, b"test cover")
        self.assertEqual(self.client.get(reverse("public-hostel-photo", args=[self.pending.pk, self.private_cover.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("public-hostel-photo", args=[self.approved.pk, self.private_cover.pk])).status_code, 404)
        fetch.assert_called_once()

    def test_only_owner_can_read_or_edit_manager_listing(self):
        payload = {"latitude": "5.5", "longitude": "-1.5"}
        self.assertEqual(self.client.patch(self.detail, payload).status_code, 401)
        for user in (self.student, self.admin):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.patch(self.detail, payload).status_code, 403)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.detail).status_code, 404)
        self.assertEqual(self.client.patch(self.detail, payload).status_code, 404)
        self.assertEqual(self.client.get(self.manager_hostels).json()["results"], [])
        self.approved.refresh_from_db()
        self.assertEqual(self.approved.latitude, Decimal("5.125001"))

    def test_manager_creates_pending_listing_and_persists_location(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.manager_hostels, {
            "name": "New fixture", "description": "Example", "address": "Fixture address", "area": "Test area",
            "latitude": "5.123456", "longitude": "-1.234567", "publication_status": "published",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.json())
        listing = Hostel.objects.get(pk=response.json()["id"])
        self.assertEqual(listing.manager, self.manager)
        self.assertEqual(listing.publication_status, "pending")
        self.assertEqual(listing.longitude, Decimal("-1.234567"))
        update = self.client.patch(self.detail, {"latitude": "0", "longitude": "0"}, format="json")
        self.assertEqual(update.status_code, 200, update.json())
        self.assertEqual(self.client.get(self.detail).json()["latitude"], "0.000000")
        self.assertEqual(self.client.patch(self.detail, {"latitude": None, "longitude": None}, format="json").status_code, 200)
        self.approved.refresh_from_db()
        self.assertIsNone(self.approved.latitude)

    def test_rejects_partial_invalid_and_out_of_range_coordinates(self):
        self.client.force_authenticate(self.owner)
        for latitude, longitude in ((None, "-1"), ("90.000001", "0"), ("0", "-180.000001"), ("NaN", "0"), ("1.0000001", "0")):
            with self.subTest(latitude=latitude, longitude=longitude):
                response = self.client.patch(self.detail, {"latitude": latitude, "longitude": longitude}, format="json")
                self.assertEqual(response.status_code, 400, response.json())
        self.approved.refresh_from_db()
        self.assertEqual(self.approved.latitude, Decimal("5.125001"))
