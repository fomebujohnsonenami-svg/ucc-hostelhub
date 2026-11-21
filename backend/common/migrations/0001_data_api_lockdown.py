from django.db import migrations

# Explicit list so new tables get an explicit access decision in their migration.
TABLES = (
    "profiles", "manager_profiles", "hostels", "hostel_images", "room_types",
    "amenities", "hostel_amenities", "saved_hostels", "roommate_profiles",
    "conversations", "conversation_participants", "messages", "subscription_plans",
    "manager_subscriptions", "moderation_reports",
    "django_migrations", "django_content_type", "auth_permission", "auth_group",
    "auth_group_permissions", "auth_user", "auth_user_groups", "auth_user_user_permissions",
)
API_ROLES = ("anon", "authenticated", "service_role")


def lock_down(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    quote = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT rolname FROM pg_roles WHERE rolname IN (%s, %s, %s)", API_ROLES)
        roles = ["PUBLIC", *(quote(row[0]) for row in cursor.fetchall())]
        for table in TABLES:
            name = quote(table)
            cursor.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
            # No allow policies. The owning Django connection can still perform CRUD.
            cursor.execute(f"REVOKE ALL PRIVILEGES ON TABLE {name} FROM {', '.join(roles)}")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("hostels", "0001_initial"),
        ("messaging", "0001_initial"),
        ("moderation", "0001_initial"),
        ("roommates", "0001_initial"),
        ("subscriptions", "0001_initial"),
    ]
    operations = [migrations.RunPython(lock_down, migrations.RunPython.noop)]
