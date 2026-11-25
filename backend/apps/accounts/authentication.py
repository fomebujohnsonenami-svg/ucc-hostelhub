from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import LoginSession


def issue_session(credential):
    token = token_urlsafe(32)
    LoginSession.objects.create(
        digest=sha256(token.encode()).hexdigest(),
        credential=credential,
        expires_at=timezone.now() + timedelta(days=7),
    )
    return token


class LocalAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b"bearer":
            return None
        if len(header) != 2 or len(header[1]) != 43:
            raise AuthenticationFailed("Invalid session. Sign in again.")
        session = LoginSession.objects.select_related("credential__profile").filter(
            pk=sha256(header[1]).hexdigest(), expires_at__gt=timezone.now(),
        ).first()
        if session is None:
            raise AuthenticationFailed("Invalid or expired session. Sign in again.")
        return session.credential.profile, session

    def authenticate_header(self, request):
        return "Bearer"
