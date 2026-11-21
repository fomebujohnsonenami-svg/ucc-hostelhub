from decimal import Decimal
from uuid import UUID, uuid5

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.accounts.models import ManagerProfile, Profile
from apps.hostels.models import Amenity, Hostel, RoomType, SavedHostel
from apps.messaging.models import Conversation, ConversationParticipant, Message
from apps.roommates.models import RoommateProfile
from common.models import VerificationStatus
from common.supabase_admin import verified_auth_user

STUDENT_ID = UUID("b6f76c2a-dfa1-4e43-aea3-e96067aca208")
MANAGER_ID = UUID("0ca829dd-ebc5-41e0-b241-92aba191743a")
HOSTEL_ID = UUID("447ea149-42c5-495b-9489-cc73657a7990")
CONVERSATION_ID = UUID("bc40adc8-6cc7-4917-bf8d-dd197c9537f0")
PEER_ID = uuid5(STUDENT_ID, "presentation-peer")

# Name, area, available beds per room type, and illustrative semester prices.
HOSTELS = (
    ("Atlantic View Hostel", "Amamoma", (3, 1), (900, 1200)),
    ("Coastal Courtyard", "Kwaprow", (2, 0), (780, 1050)),
    ("Palm Study Lodge", "Apewosika", (5, 2), (850, 1100)),
    ("Cape Breeze Hall", "Ayensu", (0, 0), (720, 990)),
    ("Lagoon Terrace", "Amamoma", (4, 3), (950, 1350)),
)
ACCOUNTS = (
    (MANAGER_ID, "demo-manager", "Demo Manager", Profile.Role.MANAGER),
    (STUDENT_ID, "demo-student", "Demo Student", Profile.Role.STUDENT),
    (PEER_ID, "demo-peer", "Demo Roommate", Profile.Role.STUDENT),
)


class Command(BaseCommand):
    help = "Seed five fictional hostels and associated presentation records."

    def add_arguments(self, parser):
        for argument in ("manager-auth-id", "student-auth-id", "peer-auth-id"):
            parser.add_argument(f"--{argument}")

    def handle(self, *args, **options):
        ids = [options[name] for name in ("manager_auth_id", "student_auth_id", "peer_auth_id")]
        if any(ids):
            if not all(ids) or not settings.DEMO_SEED_ENABLED or not settings.PRESENTATION_MODE or connection.vendor != "postgresql":
                raise CommandError("Hosted seeding requires all three Auth UUIDs, PostgreSQL, DEMO_SEED_ENABLED and PRESENTATION_MODE.")
            ids = [verified_auth_user(user_id) for user_id in ids]
        elif settings.DEBUG and connection.vendor == "sqlite" and "memory" not in str(connection.settings_dict["NAME"]):
            ids = [item[0] for item in ACCOUNTS]
        else:
            raise CommandError("Use persistent SQLite with DEBUG for local data, or explicitly configure the hosted demonstration project.")
        if len(set(ids)) != 3:
            raise CommandError("The three demonstration accounts must be distinct.")
        self.seed(ids)
        self.stdout.write(self.style.SUCCESS("Five fictional listings and presentation records are ready."))

    @transaction.atomic
    def seed(self, ids):
        profiles = []
        for user_id, (_, username, full_name, role) in zip(ids, ACCOUNTS):
            if Profile.objects.filter(username=username).exclude(pk=user_id).exists():
                raise CommandError(f"The reserved demo username {username} belongs to another profile.")
            profile, _ = Profile.objects.get_or_create(pk=user_id, defaults={
                "username": username, "full_name": full_name, "role": role,
            })
            if (profile.username, profile.full_name, profile.role) != (username, full_name, role):
                raise CommandError(f"Use a fresh Auth account or the exact existing demonstration profile for {username}.")
            profiles.append(profile)

        owner, student, peer = profiles
        manager, _ = ManagerProfile.objects.get_or_create(user=owner, defaults={
            "business_name": "Demo Hostel Management", "verification_status": VerificationStatus.VERIFIED,
        })
        first = None
        for index, (name, area, counts, prices) in enumerate(HOSTELS):
            hostel_id = HOSTEL_ID if index == 0 else uuid5(HOSTEL_ID, name)
            defaults = {
                "manager": manager, "name": f"Demo {name}", "area": area,
                "address": "Fictional listing for the university presentation",
                "description": "Fictional student accommodation. No reservations are accepted.",
                "publication_status": Hostel.PublicationStatus.PUBLISHED, "verification_status": VerificationStatus.VERIFIED,
                "featured": index == 0,
            }
            if index == 0:
                # Public UCC-area reference point for directions, not a property address.
                defaults.update(latitude=Decimal("5.115000"), longitude=Decimal("-1.289000"),
                                address="UCC area demonstration point",
                                description="Fictional hostel. Directions show the UCC demonstration point, not a property.")
            hostel, _ = Hostel.objects.get_or_create(pk=hostel_id, defaults=defaults)
            if hostel.manager_id != manager.pk or hostel.name != defaults["name"]:
                raise CommandError("A reserved demo listing ID belongs to another listing.")
            if hostel.description == "Fictional student accommodation for local development.":
                for field in ("address", "description", "publication_status", "verification_status", "featured", "latitude", "longitude"):
                    setattr(hostel, field, defaults[field])
                hostel.save()
            hostel.amenities.add(*Amenity.objects.filter(name__in=("Study Area", "Wi-Fi")))
            for room_name, capacity, available, price in zip(("Demo Double", "Demo Single"), (2, 1), counts, prices):
                RoomType.objects.get_or_create(hostel=hostel, name=room_name, defaults={
                    "capacity": capacity, "price_per_bed": Decimal(price), "total_rooms": 5, "available_beds": available,
                })
            if first is None:
                first = hostel

        SavedHostel.objects.get_or_create(student=student, hostel=first)
        for profile, name, area, preferences in (
            (student, "Demo Student", "Amamoma", ["Quiet", "Studious"]),
            (peer, "Demo Roommate", "Amamoma", ["Quiet", "Clean"]),
        ):
            RoommateProfile.objects.get_or_create(student=profile, defaults={
                "display_name": name, "preferred_area": area, "student_level": "300",
                "budget_min": Decimal("700.00"), "budget_max": Decimal("1050.00"),
                "lifestyle_preferences": preferences, "description": "Fictional roommate profile for the presentation.",
                "visibility": RoommateProfile.Visibility.PUBLIC,
            })

        pairs = (
            (CONVERSATION_ID, Conversation.Type.HOSTEL, first, student, owner, "Demo inquiry about a double room."),
            (uuid5(CONVERSATION_ID, "second-inquiry"), Conversation.Type.HOSTEL, first, peer, owner, "Demo inquiry: is a viewing possible?"),
            (uuid5(CONVERSATION_ID, "roommate"), Conversation.Type.ROOMMATE, None, student, peer, "Demo roommate inquiry about sharing near UCC."),
        )
        for thread_id, kind, listing, sender, recipient, body in pairs:
            thread, created = Conversation.objects.get_or_create(pk=thread_id, defaults={
                "conversation_type": kind, "hostel": listing,
            })
            if not created and (thread.conversation_type != kind or thread.hostel_id != (listing.pk if listing else None)
                                or set(thread.participants.values_list("pk", flat=True)) != {sender.pk, recipient.pk}):
                raise CommandError("A reserved demo conversation ID belongs to another conversation.")
            for profile in (sender, recipient):
                ConversationParticipant.objects.get_or_create(conversation=thread, user=profile)
            Message.objects.get_or_create(conversation=thread, sender=sender, body=body)
