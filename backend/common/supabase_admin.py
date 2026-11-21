from uuid import UUID

import httpx
from django.conf import settings
from django.core.management.base import CommandError

from apps.accounts.authentication import project_url


def verified_auth_user(user_id):
    """Check a server-supplied UUID against the configured Supabase Auth project."""
    try:
        user_id = UUID(str(user_id))
        origin = project_url()
    except (ValueError, AttributeError):
        raise CommandError("Supply a valid Auth UUID and configure SUPABASE_URL.") from None

    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not key:
        raise CommandError("Set the server-only SUPABASE_SERVICE_ROLE_KEY.")
    try:
        response = httpx.get(
            f"{origin}/auth/v1/admin/users/{user_id}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10.0,
        )
        response.raise_for_status()
        user = response.json()
    except (httpx.HTTPError, ValueError):
        raise CommandError(f"Could not verify Auth user {user_id} in the configured Supabase project.") from None
    if not isinstance(user, dict) or user.get("id") != str(user_id) or not user.get("email_confirmed_at"):
        raise CommandError(f"Auth user {user_id} must exist and have a confirmed email.")
    return user_id
