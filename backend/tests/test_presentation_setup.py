from io import StringIO
from uuid import uuid4

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings

from apps.accounts.models import LocalCredential, Profile
from apps.hostels.models import Hostel, RoomType
from apps.messaging.models import Message
from apps.roommates.models import RoommateProfile


class SetupTests(TestCase):
    def test_bootstrap_requires_explicit_promotion_of_a_matching_local_account(self):
        user = Profile.objects.create(id=uuid4(), username="operator", full_name="Operator")
        LocalCredential.objects.create(profile=user, email="operator@example.com", password_hash="!")
        args = ("--email", "operator@example.com", "--username", user.username)
        with self.assertRaisesRegex(CommandError, "Explicitly authorize"):
            call_command("bootstrap_admin", *args, stdout=StringIO())
        user.refresh_from_db()
        self.assertEqual(user.role, Profile.Role.STUDENT)
        call_command("bootstrap_admin", *args, "--promote-existing", stdout=StringIO())
        user.refresh_from_db()
        self.assertEqual(user.role, Profile.Role.ADMIN)

    @override_settings(DEMO_SEED_ENABLED=True, PRESENTATION_MODE=True)
    def test_hosted_seed_is_repeatable_and_uses_local_account_ids(self):
        if connection.vendor != "postgresql":
            self.skipTest("Hosted presentation seeding requires PostgreSQL.")
        from common.management.commands.seed_demo import ACCOUNTS

        ids = []
        for _, username, full_name, role in ACCOUNTS:
            profile = Profile.objects.create(id=uuid4(), username=username, full_name=full_name, role=role)
            LocalCredential.objects.create(profile=profile, email=f"{username}@example.com", password_hash="!")
            ids.append(profile.pk)
        options = dict(manager_profile_id=str(ids[0]), student_profile_id=str(ids[1]), peer_profile_id=str(ids[2]))
        for _ in range(2):
            call_command("seed_demo", **options, stdout=StringIO())
        self.assertSetEqual(set(Profile.objects.values_list("pk", flat=True)), set(ids))
        self.assertEqual(Hostel.objects.filter(name__startswith="Demo ", publication_status="published", verification_status="verified").count(), 5)
        self.assertEqual(RoomType.objects.count(), 10)
        self.assertGreater(RoomType.objects.values("available_beds").distinct().count(), 3)
        self.assertEqual(RoommateProfile.objects.filter(visibility="public").count(), 2)
        self.assertEqual(Message.objects.count(), 3)

    def test_hosted_seed_refuses_without_opt_in(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", manager_profile_id=str(uuid4()), student_profile_id=str(uuid4()),
                         peer_profile_id=str(uuid4()), stdout=StringIO())
