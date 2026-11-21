import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import Profile

ISSUER = "https://project.example.com/auth/v1"
SECRET = "unit-test-only-symmetric-key-long-enough-for-hs256"


@override_settings(SUPABASE_URL="https://project.example.com", SUPABASE_JWT_SECRET=SECRET)
class AuthTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(id=uuid4(), full_name="Student", username="student")
        self.url = reverse("profile-avatar")

    def token(self, *, key=SECRET, algorithm="HS256", headers=None, **claims):
        payload = {
            "sub": str(self.profile.pk), "iss": ISSUER, "role": "authenticated",
            "aud": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(minutes=2),
        }
        return jwt.encode(payload | claims, key, algorithm=algorithm, headers=headers)

    def get(self, token):
        return self.client.get(self.url, headers={"Authorization": f"Bearer {token}"})

    def test_only_matching_project_access_tokens_work(self):
        self.assertEqual(self.get(self.token()).status_code, 404)  # Verified, no avatar.
        for token in (
            self.token(key="another-symmetric-test-key-of-sufficient-length"),
            self.token(iss="https://other.example.com/auth/v1"),
            self.token(exp=datetime.now(timezone.utc) - timedelta(seconds=1)),
            self.token(aud="anon"),
            self.token(role="service_role"),
            self.token(sub=str(uuid4())),
            self.token(headers={"typ": "refresh"}),
        ):
            with self.subTest(token_prefix=token[:10]):
                self.assertEqual(self.get(token).status_code, 401)

    def test_frontend_role_claim_cannot_elevate_profile(self):
        from apps.accounts.models import ManagerProfile
        from apps.hostels.models import Hostel

        owner = Profile.objects.create(id=uuid4(), full_name="Owner", username="owner", role=Profile.Role.MANAGER)
        manager = ManagerProfile.objects.create(user=owner, business_name="Test")
        hostel = Hostel.objects.create(manager=manager, name="Test Hostel")
        response = self.client.post(reverse("hostel-image-upload", args=[hostel.pk]), headers={
            "Authorization": f"Bearer {self.token(app_metadata={'role': 'admin'})}",
        })
        self.assertEqual(response.status_code, 403)

    @override_settings(SUPABASE_JWT_SECRET="")
    @patch("apps.accounts.authentication.jwt.PyJWKClient.fetch_data")
    def test_asymmetric_project_jwks_verifies_signature(self, fetch):
        from apps.accounts.authentication import jwks_client

        jwks_client.cache_clear()
        self.addCleanup(jwks_client.cache_clear)
        key = ec.generate_private_key(ec.SECP256R1())
        jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key()))
        fetch.return_value = {"keys": [jwk | {"kid": "test-key", "use": "sig", "alg": "ES256"}]}
        self.assertEqual(self.get(self.token(key=key, algorithm="ES256", headers={"kid": "test-key"})).status_code, 404)
        other = ec.generate_private_key(ec.SECP256R1())
        self.assertEqual(self.get(self.token(key=other, algorithm="ES256", headers={"kid": "test-key"})).status_code, 401)
        self.assertEqual(self.get(self.token()).status_code, 401)
