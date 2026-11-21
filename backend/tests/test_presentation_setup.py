from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings

from apps.accounts.models import Profile
from apps.hostels.models import Hostel, RoomType
from apps.messaging.models import Message
from apps.roommates.models import RoommateProfile


class SetupTests(TestCase):
    @patch("common.management.commands.bootstrap_admin.verified_auth_user")
    def test_bootstrap_validates_auth_identity_and_requires_explicit_promotion(self, lookup):
        user = Profile.objects.create(id=uuid4(), username="operator", full_name="Operator")
        lookup.return_value = user.pk
        args = ("--auth-id", str(user.pk), "--username", user.username, "--full-name", user.full_name)
        with self.assertRaisesRegex(CommandError, "Explicitly authorize"):
            call_command("bootstrap_admin", *args, stdout=StringIO())
        user.refresh_from_db()
        self.assertEqual(user.role, Profile.Role.STUDENT)
        call_command("bootstrap_admin", *args, "--promote-existing", stdout=StringIO())
        user.refresh_from_db()
        self.assertEqual(user.role, Profile.Role.ADMIN)
        lookup.assert_called_with(str(user.pk))

    @patch("common.management.commands.bootstrap_admin.verified_auth_user")
    def test_bootstrap_creates_an_admin_for_a_confirmed_identity(self, lookup):
        lookup.return_value = uuid4()
        call_command("bootstrap_admin", "--auth-id", str(lookup.return_value), "--username", "new-admin",
                     "--full-name", "Presentation Administrator", stdout=StringIO())
        self.assertEqual(Profile.objects.get(pk=lookup.return_value).role, Profile.Role.ADMIN)

    @override_settings(DEMO_SEED_ENABLED=True, PRESENTATION_MODE=True)
    @patch("common.management.commands.seed_demo.verified_auth_user")
    def test_hosted_seed_is_repeatable_and_uses_confirmed_account_ids(self, lookup):
        if connection.vendor != "postgresql":
            self.skipTest("Hosted presentation seeding requires PostgreSQL.")
        ids = [uuid4(), uuid4(), uuid4()]
        lookup.side_effect = [*ids, *ids]
        options = dict(manager_auth_id=str(ids[0]), student_auth_id=str(ids[1]), peer_auth_id=str(ids[2]))
        for _ in range(2):
            call_command("seed_demo", **options, stdout=StringIO())
        self.assertSetEqual(set(Profile.objects.values_list("pk", flat=True)), set(ids))
        self.assertEqual(Hostel.objects.filter(name__startswith="Demo ", publication_status="published", verification_status="verified").count(), 5)
        self.assertEqual(RoomType.objects.count(), 10)
        self.assertGreater(RoomType.objects.values("available_beds").distinct().count(), 3)
        self.assertEqual(RoommateProfile.objects.filter(visibility="public").count(), 2)
        self.assertEqual(Message.objects.count(), 3)

    @patch("common.management.commands.seed_demo.verified_auth_user")
    def test_hosted_seed_refuses_without_opt_in(self, lookup):
        with self.assertRaises(CommandError):
            call_command("seed_demo", manager_auth_id=str(uuid4()), student_auth_id=str(uuid4()),
                         peer_auth_id=str(uuid4()), stdout=StringIO())
        lookup.assert_not_called()
