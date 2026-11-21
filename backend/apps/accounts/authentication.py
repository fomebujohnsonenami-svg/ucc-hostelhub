from functools import lru_cache
from urllib.parse import urlsplit
from uuid import UUID

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import Profile


@lru_cache(maxsize=8)
def jwks_client(issuer):
    return jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", timeout=5)


def project_url():
    url = urlsplit(settings.SUPABASE_URL)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError("SUPABASE_URL must be an HTTPS project origin.")
    return settings.SUPABASE_URL


def access_token_subject(token):
    issuer = f"{project_url()}/auth/v1"
    header = jwt.get_unverified_header(token)
    if header.get("typ") != "JWT":
        raise jwt.InvalidTokenError("Invalid access token type.")

    # Project configuration chooses legacy signing, never a fallback after JWKS failure.
    algorithm = header.get("alg")
    if settings.SUPABASE_JWT_SECRET:
        if algorithm != "HS256":
            raise jwt.InvalidAlgorithmError()
        key = settings.SUPABASE_JWT_SECRET
    elif algorithm in {"ES256", "RS256"} and header.get("kid"):
        key = jwks_client(issuer).get_signing_key_from_jwt(token)
    else:
        raise jwt.InvalidAlgorithmError()

    claims = jwt.decode(
        token, key, algorithms=[algorithm], audience="authenticated", issuer=issuer,
        options={"require": ["sub", "iss", "aud", "exp", "role"]},
    )
    if claims["role"] != "authenticated":
        raise jwt.InvalidTokenError("Expected an authenticated user access token.")
    return UUID(claims["sub"])


class SupabaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b"bearer":
            return None
        if len(header) != 2:
            raise AuthenticationFailed("Invalid authorization header.")
        try:
            subject = access_token_subject(header[1])
        except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
            raise AuthenticationFailed("Invalid or expired Supabase access token.") from None

        profile = Profile.objects.filter(pk=subject).first()
        if profile is None:
            raise AuthenticationFailed("No application profile is available for this account.")
        return profile, None

    def authenticate_header(self, request):
        return "Bearer"
