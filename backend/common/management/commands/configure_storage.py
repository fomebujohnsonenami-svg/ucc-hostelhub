from urllib.parse import quote

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from common.storage import IMAGE_TYPE, MAX_IMAGE_BYTES, StorageUnavailable, storage_request
from common.storage_policies import restrict_direct_storage_access


class Command(BaseCommand):
    help = "Create or update the two private Supabase Storage buckets."

    def handle(self, *args, **options):
        buckets = (settings.SUPABASE_HOSTEL_BUCKET, settings.SUPABASE_AVATAR_BUCKET)
        if not all(buckets) or buckets[0] == buckets[1]:
            raise CommandError("Set distinct, nonempty hostel and avatar bucket names.")
        restrict_direct_storage_access(buckets)
        for bucket in buckets:
            endpoint = f"bucket/{quote(bucket, safe='')}"
            limits = {"public": False, "file_size_limit": MAX_IMAGE_BYTES, "allowed_mime_types": [IMAGE_TYPE]}
            try:
                response = storage_request("GET", endpoint, allowed=(200, 404))
                if response.status_code == 404:
                    storage_request("POST", "bucket", json={"id": bucket, "name": bucket, **limits})
                else:
                    storage_request("PUT", endpoint, json=limits)
            except StorageUnavailable:
                raise CommandError(f"Could not configure bucket {bucket}. Check the project URL, key, and network.") from None
            self.stdout.write(self.style.SUCCESS(f"Configured private bucket {bucket}."))
