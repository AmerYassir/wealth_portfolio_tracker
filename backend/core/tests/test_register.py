from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class RegisterTests(TestCase):
    def test_register_returns_tokens_and_creates_user(self):
        c = APIClient()
        r = c.post("/api/token/register/", {"username": "newbie", "password": "correcthorse"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="newbie").exists())

    def test_duplicate_username_rejected(self):
        User = get_user_model()
        User.objects.create_user("taken", password="x")
        c = APIClient()
        r = c.post("/api/token/register/", {"username": "taken", "password": "correcthorse"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_short_password_rejected(self):
        c = APIClient()
        r = c.post("/api/token/register/", {"username": "shorty", "password": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_new_user_has_no_portfolios(self):
        c = APIClient()
        r = c.post("/api/token/register/", {"username": "blank", "password": "correcthorse"}, format="json")
        token = r.data["access"]
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r2 = c.get("/api/v1/portfolios/")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data, [])
