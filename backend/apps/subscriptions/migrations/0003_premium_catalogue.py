from decimal import Decimal

from django.db import migrations


def seed_plans(apps, schema_editor):
    plans = apps.get_model("subscriptions", "SubscriptionPlan").objects.using(schema_editor.connection.alias)
    entries = [
        ("student", "Student Premium", "20.00", [
            "Send direct messages to hostel managers",
            "Message potential roommates",
            "Participate in existing conversations",
            "Use the full in-app messaging experience",
            "View and manage your message history",
        ]),
        ("manager", "Hostel Manager Premium", "50.00", [
            "Feature eligible hostel listings",
            "Display a premium badge on promoted listings",
            "Appear in designated promotional sections",
            "Promote hostel cards on the homepage",
            "View basic listing inquiry analytics",
            "Promote listings within hostel discovery",
        ]),
    ]
    for audience, name, price, features in entries:
        plans.update_or_create(name=name, billing_period="month", defaults={
            "audience": audience, "price": Decimal(price), "features": features, "is_active": True,
        })


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0002_subscriptionplan_audience")]
    operations = [migrations.RunPython(seed_plans, migrations.RunPython.noop)]
