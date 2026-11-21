from hashlib import sha256

from django.core.management.base import CommandError
from django.db import DatabaseError, connection, transaction
from psycopg import sql


def restrict_direct_storage_access(buckets):
    if connection.vendor != "postgresql":
        raise CommandError("Connect Django to the Supabase PostgreSQL project before configuring storage.")

    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                """SELECT relrowsecurity FROM pg_class
                   WHERE oid = to_regclass('storage.objects')"""
            )
            if cursor.fetchone() != (True,):
                raise CommandError("The connected project must have RLS enabled on Supabase storage.objects.")

            for bucket in buckets:
                # A separate name per bucket keeps previously protected buckets private
                # if the deployment later selects different buckets.
                name = sql.Identifier(f"ucc_backend_only_{sha256(bucket.encode()).hexdigest()[:24]}").as_string()
                value = sql.Literal(bucket).as_string()
                cursor.execute(f"DROP POLICY IF EXISTS {name} ON storage.objects")
                cursor.execute(
                    f"CREATE POLICY {name} ON storage.objects AS RESTRICTIVE FOR ALL "
                    "TO anon, authenticated "
                    f"USING (bucket_id <> {value}) WITH CHECK (bucket_id <> {value})"
                )
    except DatabaseError:
        raise CommandError(
            "Could not apply the bucket policies. Use the Supabase database role allowed to manage policies on storage.objects."
        ) from None
