from django.contrib.auth.hashers import check_password
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import LocalCredential, LoginSession, ManagerProfile, Profile


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthTests(APITestCase):
    fields = {
        "email": "Demo@Example.com", "password": "Demo password 42!",
        "full_name": "Demo Student", "username": "demo-student", "role": "student",
    }

    def register(self, **changes):
        return self.client.post("/api/auth/register/", self.fields | changes, format="json")

    def login(self, password):
        return self.client.post("/api/auth/login/", {"email": "DEMO@example.com", "password": password}, format="json")

    def test_registration_login_and_logout(self):
        registration = self.register()
        self.assertEqual(registration.status_code, 201, registration.data)
        credential = LocalCredential.objects.get()
        self.assertEqual(credential.email, "demo@example.com")
        self.assertNotEqual(credential.password_hash, self.fields["password"])
        self.assertTrue(check_password(self.fields["password"], credential.password_hash))
        self.assertFalse(LoginSession.objects.filter(pk=registration.data["token"]).exists())

        self.assertEqual(self.login("incorrect").status_code, 401)
        login = self.login(self.fields["password"])
        self.assertEqual(login.status_code, 200, login.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['token']}")
        self.assertEqual(self.client.get("/api/me/").data["id"], str(credential.profile_id))
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_manager_role_and_duplicate_signup(self):
        self.assertEqual(self.register(role="admin").status_code, 400)
        self.assertEqual(self.register(role="manager").status_code, 400)
        response = self.register(role="manager", business_name="Demo Hostels")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(ManagerProfile.objects.get().business_name, "Demo Hostels")
        self.assertEqual(self.register(username="another").status_code, 400)
        self.assertEqual(Profile.objects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        self.assertEqual(self.client.patch("/api/me/", {"role": "admin"}, format="json").data["role"], "manager")
        self.assertEqual(self.client.get("/api/dashboard/admin/").status_code, 403)

    def test_expired_session_is_rejected(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.data)
        LoginSession.objects.update(expires_at=timezone.now())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        self.assertEqual(self.client.get("/api/me/").status_code, 401)
