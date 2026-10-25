"""Phase 4 security proof, adapted to the AGUIServer tool pattern.

Tools read the user from a ContextVar set by get_user(). These tests set the
ContextVar the same way the view does, then call the tool functions directly.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from agent.agent_tools import (
    get_portfolio_summary,
    list_my_portfolios,
    query_transactions,
    set_current_user,
    add_asset,
    log_transaction,
)
from core.models import Asset, Membership, Portfolio, Transaction


class ToolIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("a_owner", password="x")
        cls.viewer = User.objects.create_user("a_viewer", password="x")

        cls.shared = Portfolio.objects.create(name="Shared", created_by=cls.owner)
        cls.hidden = Portfolio.objects.create(name="Hidden", created_by=cls.owner)
        Membership.objects.create(user=cls.owner, portfolio=cls.shared, role="OWNER")
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
        Transaction.objects.create(
            asset=cls.shared_asset, type="BUY", amount=100,
            occurred_at="2024-01-01T00:00:00Z",
        )
        Transaction.objects.create(
            asset=cls.hidden_asset, type="BUY", amount=100,
            occurred_at="2024-01-01T00:00:00Z",
        )

    def setUp(self):
        set_current_user(AnonymousUser())

    def _as(self, user):
        set_current_user(user)

    def test_viewer_lists_only_shared(self):
        self._as(self.viewer)
        result = list_my_portfolios()
        self.assertEqual([p["name"] for p in result], ["Shared"])

    def test_owner_lists_both(self):
        self._as(self.owner)
        result = list_my_portfolios()
        self.assertEqual(sorted(p["name"] for p in result), ["Hidden", "Shared"])

    def test_viewer_denied_on_hidden(self):
        """THE security proof."""
        self._as(self.viewer)
        result = get_portfolio_summary(self.hidden.id)
        self.assertEqual(result, {"error": "not found or access denied"})

    def test_owner_succeeds_on_hidden(self):
        self._as(self.owner)
        result = get_portfolio_summary(self.hidden.id)
        self.assertNotIn("error", result)
        self.assertEqual(result["name"], "Hidden")
        self.assertEqual(result["role"], "OWNER")

    def test_viewer_denied_on_hidden_transactions(self):
        self._as(self.viewer)
        result = query_transactions(self.hidden.id)
        self.assertEqual(result, {"error": "not found or access denied"})

    def test_viewer_sees_shared_transactions(self):
        self._as(self.viewer)
        result = query_transactions(self.shared.id)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["asset_symbol"], "AAPL")

    def test_anonymous_raises(self):
        set_current_user(AnonymousUser())
        with self.assertRaises(PermissionError):
            list_my_portfolios()


def test_viewer_cannot_add_asset(self):
    self._as(self.viewer)
    result = add_asset(self.shared.id, "STOCK", "MSFT", "1", "100")
    self.assertEqual(result, {"error": "not found or access denied"})

def test_editor_can_add_asset(self):
    self._as(self.editor)
    result = add_asset(self.shared.id, "STOCK", "MSFT", "1", "100")
    self.assertIn("id", result)
    self.assertEqual(result["symbol"], "MSFT")

def test_viewer_cannot_log_transaction(self):
    self._as(self.viewer)
    result = log_transaction(self.shared.id, self.shared_asset.id, "BUY", "100", "2024-06-01")
    self.assertEqual(result, {"error": "not found or access denied"})

def test_editor_can_log_transaction(self):
    self._as(self.editor)
    result = log_transaction(self.shared.id, self.shared_asset.id, "BUY", "100", "2024-06-01")
    self.assertIn("id", result)
    self.assertEqual(result["type"], "BUY")