from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Amenity, Hostel, HostelAmenity, RoomType, SavedHostel
from apps.messaging.models import Conversation, ConversationParticipant
from apps.roommates.models import RoommateProfile
from apps.subscriptions.models import ManagerSubscription, SubscriptionPlan


class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = Profile.objects.create(id=uuid4(), full_name="Sample Student", username="sample-student")
        owner = Profile.objects.create(id=uuid4(), full_name="Sample Owner", username="sample-owner", role=Profile.Role.MANAGER)
        cls.manager = ManagerProfile.objects.create(user=owner, business_name="Sample Management")
        cls.hostel = Hostel.objects.create(manager=cls.manager, name="Sample Hostel", area="Amamoma")

    def assert_rejected(self, model, **fields):
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.create(**fields)

    def test_favourites_and_amenities_are_unique(self):
        SavedHostel.objects.create(student=self.student, hostel=self.hostel)
        self.assert_rejected(SavedHostel, student=self.student, hostel=self.hostel)
        amenity = Amenity.objects.get(name="Wi-Fi")
        self.hostel.amenities.add(amenity)
        self.assertEqual(self.hostel.amenities.get(), amenity)
        self.assert_rejected(HostelAmenity, hostel=self.hostel, amenity=amenity)

    def test_rooms_validate_monetary_and_availability_limits(self):
        fields = {"hostel": self.hostel, "name": "Double", "capacity": 2, "total_rooms": 2, "price_per_bed": Decimal("900.55")}
        room = RoomType.objects.create(**fields, available_beds=4)
        room.refresh_from_db()
        self.assertEqual(room.price_per_bed, Decimal("900.55"))
        for changes in (
            {"available_beds": -1}, {"available_beds": 5}, {"capacity": 0},
            {"total_rooms": -1}, {"price_per_bed": Decimal("-0.01")},
        ):
            with self.subTest(changes=changes):
                self.assert_rejected(RoomType, **(fields | changes))
        with self.assertRaises(ValidationError):
            RoomType(**fields, available_beds=5).full_clean()

    def test_roommate_budget_and_one_profile_per_student(self):
        fields = {"student": self.student, "display_name": "Sample Student", "preferred_area": "Amamoma", "student_level": "200"}
        self.assert_rejected(RoommateProfile, **fields, budget_min=900, budget_max=800)
        self.assert_rejected(RoommateProfile, **fields, budget_min=-1, budget_max=900)
        item = RoommateProfile.objects.create(**fields, budget_min=700, budget_max=900)
        self.assertEqual(item.visibility, RoommateProfile.Visibility.PRIVATE)
        self.assert_rejected(RoommateProfile, **fields, budget_min=700, budget_max=900)

    def test_conversation_membership_is_unique_and_hostel_deletion_preserves_thread(self):
        conversation = Conversation.objects.create(conversation_type=Conversation.Type.HOSTEL, hostel=self.hostel)
        ConversationParticipant.objects.create(conversation=conversation, user=self.student)
        self.assert_rejected(ConversationParticipant, conversation=conversation, user=self.student)
        self.assert_rejected(Conversation, conversation_type=Conversation.Type.ROOMMATE, hostel=self.hostel)
        self.hostel.delete()
        conversation.refresh_from_db()
        self.assertIsNone(conversation.hostel)
        self.assertEqual(conversation.participants.get(), self.student)

    def test_geo_and_subscription_constraints(self):
        fields = {"manager": self.manager, "name": "Test", "area": "Amamoma"}
        self.assert_rejected(Hostel, **fields, latitude=5)
        self.assert_rejected(Hostel, **fields, latitude=91, longitude=-1)
        self.assert_rejected(SubscriptionPlan, name="Premium", price=-1, billing_period="month")
        plan = SubscriptionPlan.objects.create(name="Premium", price=20, billing_period="month")
        now = timezone.now()
        self.assert_rejected(ManagerSubscription, manager=self.manager, plan=plan, starts_at=now, expires_at=now)
