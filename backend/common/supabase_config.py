from urllib.parse import urlsplit

from django.conf import settings


def project_url():
    url = urlsplit(settings.SUPABASE_URL)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError("SUPABASE_URL must be an HTTPS project origin.")
    return settings.SUPABASE_URL
