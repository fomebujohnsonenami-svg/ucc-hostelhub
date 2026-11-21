from django.conf import settings

from common.api import require_role


def access_mode():
    # The launch preview remains open until real entitlements can be enforced.
    return "presentation" if settings.PRESENTATION_MODE else "launch_preview"


def messaging_access(user, *, starts_conversation=False):
    roles = ("student",) if starts_conversation else ("student", "manager")
    require_role(user, *roles)
    return access_mode()
