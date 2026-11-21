from uuid import uuid4

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Hostel
from apps.roommates.models import RoommateProfile
from apps.subscriptions.models import ManagerSubscription


class PremiumTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name, role in (("owner", "manager"), ("other", "manager"), ("student", "student"), ("peer", "student"), ("admin", "admin")):
            setattr(cls, name, Profile.objects.create(id=uuid4(), full_name=name.title(), username=name, role=role))
        manager = ManagerProfile.objects.create(user=cls.owner, business_name="Owner")
        ManagerProfile.objects.create(user=cls.other, business_name="Other")
        cls.hostel = Hostel.objects.create(manager=manager, name="Cape Coast Hostel", area="Kwaprow", publication_status="published", verification_status="verified")
        cls.draft = Hostel.objects.create(manager=manager, name="Pending Hostel", area="Kwaprow")
        cls.roommate = RoommateProfile.objects.create(student=cls.peer, display_name="Peer", preferred_area="Kwaprow", student_level="300",
                                                      budget_min=100, budget_max=200, visibility="public")

    @override_settings(PRESENTATION_MODE=True)
    def test_plan_prices_are_public_and_do_not_activate_any_subscriptions(self):
        response = self.client.get("/api/subscription-plans/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["access_mode"], "presentation")
        self.assertFalse(data["payments_available"])
        self.assertEqual([(plan["name"], plan["price"], plan["billing_period"]) for plan in data["plans"]], [
            ("Student Premium", "20.00", "month"), ("Hostel Manager Premium", "50.00", "month"),
        ])
        self.assertFalse(ManagerSubscription.objects.exists())

    def test_messaging_operates_in_both_server_modes_without_a_purchase(self):
        for mode in (True, False):
            with self.subTest(mode=mode), override_settings(PRESENTATION_MODE=mode):
                client = APIClient()
                status = client.get("/api/subscription-plans/", headers={"X-Presentation-Mode": "true"}).json()["access_mode"]
                self.assertEqual(status, "presentation" if mode else "launch_preview")
                self.assertEqual(client.post("/api/conversations/", {"hostel": self.hostel.pk}, format="json").status_code, 401)
                client.force_authenticate(self.student)
                for key, target in (("hostel", self.hostel), ("roommate", self.roommate)):
                    conversation = client.post("/api/conversations/", {key: str(target.pk)}, format="json")
                    self.assertIn(conversation.status_code, (200, 201))
                    path = f"/api/conversations/{conversation.json()['id']}/messages/"
                    self.assertEqual(client.post(path, {"body": "Hello"}, format="json").status_code, 201)
                    client.force_authenticate(self.other)
                    self.assertEqual(client.get(path).status_code, 404)
                    client.force_authenticate(self.owner if key == "hostel" else self.peer)
                    self.assertEqual(client.get(path).status_code, 200)
                    self.assertEqual(client.post(path, {"body": "Reply"}, format="json").status_code, 201)
                    client.force_authenticate(self.student)
                self.assertFalse(ManagerSubscription.objects.exists())

    @override_settings(PRESENTATION_MODE=True)
    def test_featured_placement_requires_ownership_and_approval(self):
        client = APIClient()
        detail = f"/api/manager/promotions/{self.hostel.pk}/"
        client.force_authenticate(self.other)
        self.assertEqual(client.patch(detail, {"featured": True}, format="json").status_code, 404)
        client.force_authenticate(self.student)
        self.assertEqual(client.patch(detail, {"featured": True}, format="json").status_code, 403)
        self.assertEqual(client.post("/api/conversations/", {"hostel": str(self.hostel.pk)}, format="json").status_code, 201)
        client.force_authenticate(self.owner)
        self.assertEqual(client.patch(f"/api/manager/promotions/{self.draft.pk}/", {"featured": True}, format="json").status_code, 400)
        self.assertEqual(client.patch(detail, {}, format="json").status_code, 400)
        self.assertEqual(client.patch(detail, {"featured": True}, format="json").status_code, 200)
        self.assertEqual(client.get("/api/manager/promotions/").json()["results"][0]["inquiries"], 1)
        client = APIClient()
        self.assertEqual(client.get("/api/hostels/?featured=yes&area=Amamoma").json()["count"], 0)
        self.assertEqual(client.get("/api/hostels/?featured=yes&area=Kwaprow").json()["results"][0]["id"], str(self.hostel.pk))
        client.force_authenticate(self.admin)
        self.assertEqual(client.post(f"/api/admin/listings/{self.hostel.pk}/", {"action": "suspend"}, format="json").status_code, 200)
        self.assertEqual(client.get("/api/hostels/?featured=yes").json()["count"], 0)
        self.hostel.refresh_from_db()
        self.assertFalse(self.hostel.featured)
        self.assertFalse(ManagerSubscription.objects.exists())
