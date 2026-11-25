from datetime import timedelta
from uuid import uuid4

from django.test import TestCase, override_settings
from django.utils import timezone as django_time
from rest_framework.test import APIClient

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Amenity, Hostel, RoomType
from apps.messaging.models import Message
from apps.moderation.models import ModerationReport
from apps.roommates.models import RoommateProfile


class PhaseFiveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        profiles = (("manager", "manager"), ("other", "manager"), ("student", "student"),
                    ("peer", "student"), ("outsider", "student"), ("admin", "admin"))
        for username, role in profiles:
            setattr(cls, username, Profile.objects.create(id=uuid4(), full_name=username.title(), username=username, role=role))
        cls.owner = ManagerProfile.objects.create(user=cls.manager, business_name="Campus Management")
        cls.other_owner = ManagerProfile.objects.create(user=cls.other, business_name="Other")
        cls.listing = Hostel.objects.create(manager=cls.owner, name="Garden Hostel", area="Amamoma", verification_status="verified", publication_status="published")
        cls.listing.amenities.add(Amenity.objects.get(name="Wi-Fi"), Amenity.objects.get(name="Laundry"))
        cls.room = RoomType.objects.create(hostel=cls.listing, name="Double", capacity=2, total_rooms=3, available_beds=2, price_per_bed=900,
                                           availability_updated_at=django_time.now() - timedelta(days=4))
        RoomType.objects.create(hostel=cls.listing, name="Single", capacity=1, total_rooms=2, available_beds=0, price_per_bed=600)
        cls.expensive = Hostel.objects.create(manager=cls.owner, name="Park Hostel", area="Amamoma", publication_status="published", verification_status="verified")
        RoomType.objects.create(hostel=cls.expensive, name="Double", capacity=2, total_rooms=2, available_beds=1, price_per_bed=1000)
        cls.pending = Hostel.objects.create(manager=cls.owner, name="Pending", area="Amamoma", publication_status="pending")

    def setUp(self):
        self.client = APIClient()

    def as_user(self, user):
        self.client.force_authenticate(user)

    def send(self, method, path, data=None):
        return getattr(self.client, method)(f"/api/{path}", data, format="json")

    def results(self, path):
        response = self.send("get", path)
        self.assertEqual(response.status_code, 200, response.json())
        return response.json()["results"]

    def test_search_filters_use_same_room_and_approved_results_are_paginated(self):
        result = self.results("hostels/?q=Garden&area=Amamoma&min=850&max=950&room=Double&available=yes&amenity=Wi-Fi&amenity=Laundry")
        self.assertEqual([item["id"] for item in result], [str(self.listing.pk)])
        self.assertEqual(self.results("hostels/?max=750&available=yes"), [])
        self.assertEqual(self.results("hostels/?amenity=Wi-Fi&amenity=Standby%20Generator"), [])
        first = self.send("get", "hostels/?sort=high&page_size=1").json()
        self.assertEqual(first["count"], 2)
        self.assertEqual(first["results"][0]["id"], str(self.expensive.pk))
        self.assertIsNotNone(first["next"])
        self.assertEqual(self.send("get", "hostels/?min=10&max=5").status_code, 400)
        self.assertEqual(self.send("get", f"hostels/{self.pending.pk}/").status_code, 404)

    def test_manager_crud_amenities_rooms_and_deletion_require_ownership(self):
        self.as_user(self.manager)
        new = self.send("post", "manager/hostels/", {"name": "New Hostel", "description": "A new listing", "area": "Kwaprow", "address": "Main Road", "amenities": ["Wi-Fi"]})
        self.assertEqual(new.status_code, 201, new.json())
        path = f"manager/hostels/{new.json()['id']}/"
        room = self.send("post", path + "rooms/", {"name": "Triple", "capacity": 3, "total_rooms": 2, "available_beds": 6, "price_per_bed": "100.05"})
        self.assertEqual(room.status_code, 201, room.json())
        self.assertEqual(room.json()["total_capacity"], 6)
        self.as_user(self.other)
        self.assertEqual(self.send("patch", path, {"amenities": ["Laundry"]}).status_code, 404)
        self.assertEqual(self.send("patch", path + f"rooms/{room.json()['id']}/", {"available_beds": 1}).status_code, 404)
        self.assertEqual(self.send("delete", path, {"confirm": True}).status_code, 404)
        self.as_user(self.manager)
        edited = self.send("patch", path, {"amenities": ["Laundry"]})
        self.assertEqual(edited.json()["amenities"], ["Laundry"])
        self.assertEqual(self.send("delete", path, {}).status_code, 400)
        self.assertEqual(self.send("delete", path + f"rooms/{room.json()['id']}/", {"confirm": True}).status_code, 204)
        self.assertEqual(self.send("delete", path, {"confirm": True}).status_code, 204)
        self.assertEqual(self.send("get", path).status_code, 404)

    @override_settings(AVAILABILITY_STALE_HOURS=48)
    def test_availability_confirmation_updates_timestamp_and_capacity_validation(self):
        path = f"manager/hostels/{self.listing.pk}/rooms/{self.room.pk}/"
        public = self.send("get", f"hostels/{self.listing.pk}/").json()
        self.assertTrue(next(room for room in public["room_types"] if room["id"] == str(self.room.pk))["availability_stale"])
        self.as_user(self.manager)
        self.assertEqual(self.send("patch", path, {"available_beds": -1}).status_code, 400)
        self.assertEqual(self.send("patch", path, {"available_beds": 7}).status_code, 400)
        response = self.send("patch", path, {"available_beds": 2})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertFalse(response.json()["availability_stale"])
        self.room.refresh_from_db()
        self.assertGreater(self.room.availability_updated_at, django_time.now() - timedelta(seconds=10))

    def test_saved_hostels_and_dashboard_counts_are_persistent(self):
        path = f"saved-hostels/{self.listing.pk}/"
        self.as_user(self.manager)
        self.assertEqual(self.send("put", path).status_code, 403)
        self.assertEqual(self.send("get", "dashboard/manager/").json(), {"hostels": 3, "rooms": 7, "beds": 3, "inquiries": 0})
        self.as_user(self.student)
        self.assertEqual(self.send("put", path).status_code, 200)
        self.assertEqual(self.send("put", path).status_code, 200)
        self.assertEqual(len(self.results("saved-hostels/")), 1)
        self.assertEqual(self.send("get", "dashboard/student/").json()["saved"], 1)
        self.assertEqual(len(self.send("get", "dashboard/student/").json()["recommended"]), 2)
        self.assertEqual(self.send("delete", path).json(), {"saved": False})
        self.assertEqual(self.send("get", "dashboard/student/").json()["saved"], 0)

    def roommate(self, user, **fields):
        defaults = {"display_name": user.full_name, "preferred_area": "Amamoma", "budget_min": 800, "budget_max": 1000,
                    "student_level": "300", "lifestyle_preferences": ["Quiet"], "visibility": "public"}
        return RoommateProfile.objects.create(student=user, **(defaults | fields))

    def test_roommate_profile_visibility_rank_and_contact(self):
        near = self.roommate(self.peer)
        self.roommate(self.outsider, budget_min=1200, budget_max=1300, preferred_area="Kwaprow", lifestyle_preferences=[])
        self.as_user(self.student)
        profile = self.send("put", "roommates/me/", {"display_name": "Student A", "preferred_area": "Amamoma",
            "budget_min": 900, "budget_max": 1100, "student_level": "300", "lifestyle_preferences": ["Quiet"]})
        self.assertEqual(profile.status_code, 201, profile.json())
        self.assertEqual(profile.json()["visibility"], "private")
        result = self.results("roommates/")
        self.assertEqual([profile["compatibility"] for profile in result], [6, 0])
        self.assertEqual(result[0]["id"], str(near.pk))
        self.assertNotIn("phone", result[0])
        self.assertEqual(self.send("post", "conversations/", {"roommate": str(near.pk)}).status_code, 201)
        self.as_user(self.outsider)
        self.assertEqual(self.send("get", f"roommates/{profile.json()['id']}/").status_code, 404)
        self.assertEqual(self.send("post", "conversations/", {"roommate": profile.json()["id"]}).status_code, 404)

    def test_messaging_authorizes_participants_and_preserves_unseen_message(self):
        self.as_user(self.student)
        start = self.send("post", "conversations/", {"hostel": str(self.listing.pk)})
        self.assertEqual(start.status_code, 201, start.json())
        self.assertEqual(self.send("post", "conversations/", {"hostel": str(self.listing.pk)}).json(), start.json())
        path = f"conversations/{start.json()['id']}/"
        first = self.send("post", path + "messages/", {"body": "Is there a bed?"})
        self.assertEqual(first.status_code, 201, first.json())
        self.assertEqual(self.send("post", path + "messages/", {"body": "Can I view it?"}).status_code, 201)
        self.assertEqual(self.send("post", path + "messages/", {"body": "   "}).status_code, 400)
        self.as_user(self.outsider)
        for method, suffix, data in (("get", "", None), ("get", "messages/", None), ("post", "messages/", {"body": "Intruder"}), ("post", "read/", {"message": first.json()["id"]})):
            self.assertEqual(self.send(method, path + suffix, data).status_code, 404)
        self.as_user(self.manager)
        self.assertEqual(self.results("conversations/")[0]["unread"], 2)
        self.assertEqual(len(self.results(path + "messages/?page_size=1")), 1)
        self.assertEqual(self.send("post", path + "read/", {"message": first.json()["id"]}).status_code, 204)
        self.assertEqual(self.results("conversations/")[0]["unread"], 1)
        self.assertEqual(self.send("post", path + "messages/", {"body": "Yes. Please visit."}).status_code, 201)
        self.assertEqual(self.send("get", "dashboard/manager/").json()["inquiries"], 1)
        self.assertEqual(Message.objects.count(), 3)

    def test_moderation_state_machine_and_report_action(self):
        admin_path = f"admin/listings/{self.pending.pk}/"
        manager_path = f"manager/hostels/{self.pending.pk}/publication/"
        self.as_user(self.manager)
        self.assertEqual(self.send("post", admin_path, {"action": "suspend"}).status_code, 403)
        self.assertEqual(self.send("post", manager_path, {"action": "publish"}).status_code, 200)
        self.as_user(self.admin)
        self.assertEqual(self.send("patch", f"admin/managers/{self.owner.pk}/", {"verification_status": "verified"}).status_code, 200)
        self.as_user(self.manager)
        self.assertEqual(self.send("post", manager_path, {"action": "unpublish"}).status_code, 200)
        self.assertEqual(self.send("post", manager_path, {"action": "publish"}).status_code, 200)
        self.as_user(self.student)
        report = self.send("post", "reports/", {"target_type": "hostel", "target_id": str(self.pending.pk), "reason": "Incorrect details"})
        self.assertEqual(report.status_code, 201, report.json())
        self.as_user(self.admin)
        self.assertEqual(self.send("get", "dashboard/admin/").json()["moderation"], 1)
        self.assertEqual(self.send("patch", f"admin/reports/{report.json()['id']}/", {"action": "remove"}).status_code, 200)
        self.assertEqual(ModerationReport.objects.get(pk=report.json()["id"]).status, "resolved")
        self.assertEqual(self.send("get", f"hostels/{self.pending.pk}/").status_code, 404)
        self.as_user(self.manager)
        self.assertEqual(self.send("post", manager_path, {"action": "publish"}).status_code, 400)

    def test_mod_report_removes_roommate_from_discovery_even_if_owner_edits(self):
        profile = self.roommate(self.peer)
        self.as_user(self.student)
        report = self.send("post", "reports/", {"target_type": "roommate", "target_id": str(profile.pk), "reason": "Reported content"})
        self.assertEqual(report.status_code, 201, report.json())
        self.as_user(self.admin)
        response = self.send("patch", f"admin/reports/{report.json()['id']}/", {"action": "remove"})
        self.assertEqual(response.status_code, 200, response.json())
        self.as_user(self.peer)
        updated = self.send("put", "roommates/me/", {"display_name": "Edited name", "preferred_area": "Amamoma",
            "budget_min": 800, "budget_max": 1100, "student_level": "300", "visibility": "public"})
        self.assertEqual(updated.status_code, 200, updated.json())
        self.assertTrue(updated.json()["moderation_hidden"])
        self.as_user(self.student)
        self.assertEqual(self.results("roommates/"), [])
        self.assertEqual(self.send("post", "conversations/", {"roommate": str(profile.pk)}).status_code, 404)

    def test_manual_action_endpoints_reject_non_object_payloads(self):
        self.as_user(self.manager)
        for method, path in (
            ("post", f"manager/hostels/{self.listing.pk}/publication/"),
            ("delete", f"manager/hostels/{self.listing.pk}/"),
            ("delete", f"manager/hostels/{self.listing.pk}/rooms/{self.room.pk}/"),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.send(method, path, []).status_code, 400)
        self.as_user(self.student)
        thread = self.send("post", "conversations/", {"hostel": str(self.listing.pk)}).json()["id"]
        self.assertEqual(self.send("post", f"conversations/{thread}/read/", []).status_code, 400)
        self.as_user(self.admin)
        self.assertEqual(self.send("post", f"admin/listings/{self.pending.pk}/", []).status_code, 400)
