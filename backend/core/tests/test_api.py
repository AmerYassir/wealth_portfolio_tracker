"""Phase 3 API tests.

Matrix covered:
- Anonymous: 401 everywhere.
- Viewer: read yes (own portfolios only), write no.
- Editor: read + write assets/tx; cannot rename/delete portfolio.
- Owner: everything.
- Cross-portfolio: serializer rejects foreign asset ids on Transaction create.
- List scoping: viewer never sees Owner Only portfolio or its contents.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Asset, Membership, Portfolio, Transaction


class APIBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("owner", password="pass1234")
        cls.editor = User.objects.create_user("editor", password="pass1234")
        cls.viewer = User.objects.create_user("viewer", password="pass1234")

        cls.shared = Portfolio.objects.create(name="Shared", created_by=cls.owner)
        cls.hidden = Portfolio.objects.create(name="Hidden", created_by=cls.owner)
        Membership.objects.create(user=cls.owner, portfolio=cls.shared, role="OWNER")
        Membership.objects.create(user=cls.editor, portfolio=cls.shared, role="EDITOR")
        Membership.objects.create(user=cls.viewer, portfolio=cls.shared, role="VIEWER")
        Membership.objects.create(user=cls.owner, portfolio=cls.hidden, role="OWNER")

        cls.shared_asset = Asset.objects.create(
            portfolio=cls.shared, type="STOCK", symbol="AAPL",
            quantity=10, cost_basis=1000,
        )
        cls.hidden_asset = Asset.objects.create(
            portfolio=cls.hidden, type="STOCK", symbol="TSLA",
            quantity=1, cost_basis=100,
        )
        cls.shared_tx = Transaction.objects.create(
            asset=cls.shared_asset, type="BUY", amount=100,
            occurred_at="2024-01-01T00:00:00Z",
        )

    def _client(self, user=None):
        c = APIClient()
        if user is not None:
            r = c.post(
                "/api/token/",
                {"username": user.username, "password": "pass1234"},
                format="json",
            )
            c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return c


class AnonymousTests(APIBase):
    def test_all_endpoints_401(self):
        c = APIClient()
        for method, url in [
            ("get", "/api/v1/portfolios/"),
            ("get", f"/api/v1/portfolios/{self.shared.id}/"),
            ("get", f"/api/v1/portfolios/{self.shared.id}/assets/"),
            ("get", f"/api/v1/portfolios/{self.shared.id}/transactions/"),
        ]:
            r = getattr(c, method)(url)
            self.assertEqual(r.status_code, 401, f"{method} {url} -> {r.status_code}")


class PortfolioListScopingTests(APIBase):
    def test_owner_sees_both(self):
        c = self._client(self.owner)
        r = c.get("/api/v1/portfolios/")
        self.assertEqual(r.status_code, 200)
        names = {p["name"] for p in r.data}
        self.assertEqual(names, {"Shared", "Hidden"})

    def test_viewer_sees_only_shared(self):
        c = self._client(self.viewer)
        r = c.get("/api/v1/portfolios/")
        self.assertEqual(r.status_code, 200)
        names = {p["name"] for p in r.data}
        self.assertEqual(names, {"Shared"})

    def test_editor_sees_only_shared(self):
        c = self._client(self.editor)
        r = c.get("/api/v1/portfolios/")
        names = {p["name"] for p in r.data}
        self.assertEqual(names, {"Shared"})


class PortfolioCreateTests(APIBase):
    def test_create_sets_created_by_and_makes_owner(self):
        c = self._client(self.editor)
        r = c.post("/api/v1/portfolios/", {"name": "New"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        new_id = r.data["id"]
        p = Portfolio.objects.get(id=new_id)
        self.assertEqual(p.created_by_id, self.editor.id)
        self.assertEqual(
            Membership.objects.get(user=self.editor, portfolio=p).role, "OWNER"
        )

    def test_created_by_cannot_be_spoofed(self):
        c = self._client(self.editor)
        r = c.post(
            "/api/v1/portfolios/",
            {"name": "Spoof", "created_by": self.owner.id},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        p = Portfolio.objects.get(id=r.data["id"])
        self.assertEqual(p.created_by_id, self.editor.id)  # not the owner


class PortfolioWritePermissionTests(APIBase):
    def test_editor_cannot_rename(self):
        c = self._client(self.editor)
        r = c.patch(
            f"/api/v1/portfolios/{self.shared.id}/",
            {"name": "Renamed"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_rename(self):
        c = self._client(self.viewer)
        r = c.patch(
            f"/api/v1/portfolios/{self.shared.id}/",
            {"name": "Renamed"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_owner_can_rename(self):
        c = self._client(self.owner)
        r = c.patch(
            f"/api/v1/portfolios/{self.shared.id}/",
            {"name": "Renamed"},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.shared.refresh_from_db()
        self.assertEqual(self.shared.name, "Renamed")

    def test_editor_cannot_delete(self):
        c = self._client(self.editor)
        r = c.delete(f"/api/v1/portfolios/{self.shared.id}/")
        self.assertEqual(r.status_code, 403)


class AssetAccessTests(APIBase):
    def test_viewer_can_list(self):
        c = self._client(self.viewer)
        r = c.get(f"/api/v1/portfolios/{self.shared.id}/assets/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual({a["symbol"] for a in r.data}, {"AAPL"})

    def test_viewer_cannot_access_hidden_portfolio(self):
        c = self._client(self.viewer)
        r = c.get(f"/api/v1/portfolios/{self.hidden.id}/assets/")
        self.assertEqual(r.status_code, 403)

    def test_viewer_cannot_create_asset(self):
        c = self._client(self.viewer)
        r = c.post(
            f"/api/v1/portfolios/{self.shared.id}/assets/",
            {"type": "STOCK", "symbol": "MSFT", "quantity": "1", "cost_basis": "1"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_editor_can_create_asset(self):
        c = self._client(self.editor)
        r = c.post(
            f"/api/v1/portfolios/{self.shared.id}/assets/",
            {"type": "STOCK", "symbol": "MSFT", "quantity": "1", "cost_basis": "1"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        a = Asset.objects.get(id=r.data["id"])
        self.assertEqual(a.portfolio_id, self.shared.id)


class TransactionAccessTests(APIBase):
    def test_viewer_can_list(self):
        c = self._client(self.viewer)
        r = c.get(f"/api/v1/portfolios/{self.shared.id}/transactions/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_viewer_cannot_create(self):
        c = self._client(self.viewer)
        r = c.post(
            f"/api/v1/portfolios/{self.shared.id}/transactions/",
            {
                "asset": self.shared_asset.id,
                "type": "SELL",
                "amount": "5",
                "occurred_at": "2024-02-01T00:00:00Z",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_editor_can_create(self):
        c = self._client(self.editor)
        r = c.post(
            f"/api/v1/portfolios/{self.shared.id}/transactions/",
            {
                "asset": self.shared_asset.id,
                "type": "SELL",
                "amount": "5",
                "occurred_at": "2024-02-01T00:00:00Z",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)

    def test_editor_cannot_create_transaction_with_foreign_asset(self):
        """The core 'reject foreign portfolio ids' rule."""
        c = self._client(self.editor)
        r = c.post(
            f"/api/v1/portfolios/{self.shared.id}/transactions/",
            {
                "asset": self.hidden_asset.id,  # belongs to a different portfolio
                "type": "SELL",
                "amount": "5",
                "occurred_at": "2024-02-01T00:00:00Z",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("asset", r.data)
