from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:5173"])
class HealthTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("health")

    def test_health_without_database_or_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_local_frontend_origin_is_allowed(self):
        origin = "http://localhost:5173"
        response = self.client.get(self.url, HTTP_ORIGIN=origin)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)

    def test_other_origin_is_not_allowed(self):
        response = self.client.get(self.url, HTTP_ORIGIN="https://example.com")
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    def test_health_is_read_only(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)
