from importlib import import_module
from unittest import skipUnless
from uuid import uuid4

from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from apps.accounts.models import Profile

lockdown = import_module("common.migrations.0001_data_api_lockdown")


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL")
class DataApiTests(TestCase):
    def test_rls_enabled_and_api_roles_have_no_crud_grants(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT c.relname, c.relrowsecurity
                   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = current_schema() AND c.relname = ANY(%s)""",
                [list(lockdown.TABLES)],
            )
            self.assertEqual(dict(cursor.fetchall()), dict.fromkeys(lockdown.TABLES, True))
            cursor.execute("SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)", [list(lockdown.API_ROLES)])
            roles = [row[0] for row in cursor.fetchall()]
            self.assertTrue(roles, "Create Data API roles on the disposable test cluster before running this test.")
            for role in roles:
                for table in lockdown.TABLES:
                    for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                        cursor.execute("SELECT has_table_privilege(%s, %s, %s)", [role, table, privilege])
                        self.assertFalse(cursor.fetchone()[0], (role, table, privilege))

    def test_rls_denies_rows_and_inserts_even_with_accidental_grants(self):
        profile_id = uuid4()
        Profile.objects.create(id=profile_id, full_name="Private", username="private", phone="012345")
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("GRANT SELECT, INSERT ON profiles TO authenticated")
            cursor.execute("SET LOCAL ROLE authenticated")
            cursor.execute("SELECT count(*) FROM profiles")
            self.assertEqual(cursor.fetchone()[0], 0)
            with self.assertRaises(DatabaseError) as error, transaction.atomic():
                cursor.execute(
                    """INSERT INTO profiles (id, full_name, username, avatar_url, avatar_storage_path, role, phone, created_at, updated_at)
                       VALUES (%s, 'Test', 'rejected', '', '', 'student', '', now(), now())""",
                    [uuid4()],
                )
            self.assertEqual(error.exception.__cause__.sqlstate, "42501")
            cursor.execute("RESET ROLE")
        self.assertEqual(Profile.objects.get(pk=profile_id).phone, "012345")

    def test_storage_policy_denies_direct_reads_and_writes_only_for_managed_buckets(self):
        from common.storage_policies import restrict_direct_storage_access

        with connection.cursor() as cursor:
            # Stand-in for the provider-managed table in a disposable database.
            cursor.execute("CREATE SCHEMA storage")
            cursor.execute("CREATE TABLE storage.objects (bucket_id text, name text)")
            cursor.execute("ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY")
            cursor.execute("CREATE POLICY broad_access ON storage.objects FOR ALL TO authenticated USING (true) WITH CHECK (true)")
            cursor.execute("GRANT USAGE ON SCHEMA storage TO authenticated")
            cursor.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON storage.objects TO authenticated")
            cursor.execute("INSERT INTO storage.objects VALUES ('avatars', 'avatar.webp'), ('hostel-images', 'hostel.webp'), ('other', 'other.webp')")
            restrict_direct_storage_access(("hostel-images", "avatars"))
            restrict_direct_storage_access(("hostel-images", "avatars"))
            cursor.execute("SET LOCAL ROLE authenticated")
            cursor.execute("SELECT bucket_id FROM storage.objects")
            self.assertEqual(cursor.fetchall(), [("other",)])
            for bucket in ("hostel-images", "avatars"):
                with self.subTest(bucket=bucket), self.assertRaises(DatabaseError) as error, transaction.atomic():
                    cursor.execute("INSERT INTO storage.objects VALUES (%s, 'new.webp')", [bucket])
                self.assertEqual(error.exception.__cause__.sqlstate, "42501")
            cursor.execute("INSERT INTO storage.objects VALUES ('other', 'new.webp')")
            cursor.execute("RESET ROLE")
            cursor.execute("SELECT count(*) FROM storage.objects")
            self.assertEqual(cursor.fetchone()[0], 4)
