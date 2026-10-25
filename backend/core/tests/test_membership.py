from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Membership, Portfolio


class MembershipAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("m_owner", password="pass1234")
        cls.editor = User.objects.create_user("m_editor", password="pass1234")
        cls.viewer = User.objects.create_user("m_viewer", password="pass1234")
        cls.outsider = User.objects.create_user("m_outsider", password="pass1234")

        cls.portfolio = Portfolio.objects.create(name="Test", created_by=cls.owner)
        Membership.objects.create(user=cls.owner, portfolio=cls.portfolio, role="OWNER")
        Membership.objects.create(user=cls.editor, portfolio=cls.portfolio, role="EDITOR")
        Membership.objects.create(user=cls.viewer, portfolio=cls.portfolio, role="VIEWER")

    def _client(self, user):
        c = APIClient()
        r = c.post("/api/token/", {"username": user.username, "password": "pass1234"}, format="json")
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return c

    def test_any_member_can_list(self):
        for u in (self.owner, self.editor, self.viewer):
            c = self._client(u)
            r = c.get(f"/api/v1/portfolios/{self.portfolio.id}/members/")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.data), 3)

    def test_outsider_cannot_list(self):
        c = self._client(self.outsider)
        r = c.get(f"/api/v1/portfolios/{self.portfolio.id}/members/")
        self.assertEqual(r.status_code, 403)

    def test_owner_can_invite_viewer(self):
        c = self._client(self.owner)
        r = c.post(
            f"/api/v1/portfolios/{self.portfolio.id}/members/",
            {"username": "m_outsider", "role": "VIEWER"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(
            Membership.objects.filter(user=self.outsider, portfolio=self.portfolio, role="VIEWER").exists()
        )

    def test_editor_cannot_invite(self):
        c = self._client(self.editor)
        r = c.post(
            f"/api/v1/portfolios/{self.portfolio.id}/members/",
            {"username": "m_outsider", "role": "VIEWER"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_invite(self):
        c = self._client(self.viewer)
        r = c.post(
            f"/api/v1/portfolios/{self.portfolio.id}/members/",
            {"username": "m_outsider", "role": "VIEWER"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_unknown_username_rejected(self):
        c = self._client(self.owner)
        r = c.post(
            f"/api/v1/portfolios/{self.portfolio.id}/members/",
            {"username": "nobody", "role": "VIEWER"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_duplicate_member_rejected(self):
        c = self._client(self.owner)
        r = c.post(
            f"/api/v1/portfolios/{self.portfolio.id}/members/",
            {"username": "m_viewer", "role": "VIEWER"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_owner_can_remove_viewer(self):
        viewer_membership = Membership.objects.get(user=self.viewer, portfolio=self.portfolio)
        c = self._client(self.owner)
        r = c.delete(f"/api/v1/portfolios/{self.portfolio.id}/members/{viewer_membership.id}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Membership.objects.filter(pk=viewer_membership.pk).exists())

    def test_editor_cannot_remove(self):
        viewer_membership = Membership.objects.get(user=self.viewer, portfolio=self.portfolio)
        c = self._client(self.editor)
        r = c.delete(f"/api/v1/portfolios/{self.portfolio.id}/members/{viewer_membership.id}/")
        self.assertEqual(r.status_code, 403)

    def test_owner_cannot_remove_self(self):
        owner_membership = Membership.objects.get(user=self.owner, portfolio=self.portfolio)
        c = self._client(self.owner)
        r = c.delete(f"/api/v1/portfolios/{self.portfolio.id}/members/{owner_membership.id}/")
        self.assertEqual(r.status_code, 400)
