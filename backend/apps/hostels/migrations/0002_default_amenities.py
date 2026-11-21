from django.db import migrations


def add_default_amenities(apps, schema_editor):
    amenity = apps.get_model("hostels", "Amenity")
    catalogue = [
        ("Wi-Fi", "wifi"), ("24/7 Security", "shield"), ("Constant Water", "droplet"),
        ("Standby Generator", "zap"), ("Study Area", "book-open"), ("Laundry", "washing-machine"),
    ]
    for name, icon in catalogue:
        amenity.objects.using(schema_editor.connection.alias).get_or_create(name=name, defaults={"icon_name": icon})


class Migration(migrations.Migration):
    dependencies = [("hostels", "0001_initial"), ("common", "0001_data_api_lockdown")]
    operations = [migrations.RunPython(add_default_amenities, migrations.RunPython.noop)]
