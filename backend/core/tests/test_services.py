"""Service-layer isolation tests.

Each test class creates the minimum data needed and asserts the service
functions enforce membership. These are the security floor for the project;
Phase 3 (API) and Phase 4 (agent tools) are only correct if these pass.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from core import services
from core.models import Asset, Membership, Portfolio, Transaction


class ServiceIsolationBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user("t_owner", password="x")
        cls.editor = User.objects.create_user("t_editor", password="x")
        cls.viewer = User.objects.create_user("t_viewer", password="x")
        cls.stranger = User.objects.create_user("t_stranger", password="x")

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
        cls.hidden_tx = Transaction.objects.create(
            asset=cls.hidden_asset, type="BUY", amount=100,
            occurred_at="2024-01-01T00:00:00Z",
        )


class GetPortfoliosForUserTests(ServiceIsolationBase):
    def test_owner_sees_both(self):
        ids = set(services.get_portfolios_for_user(self.owner).values_list("id", flat=True))
        self.assertEqual(ids, {self.shared.id, self.hidden.id})

    def test_editor_sees_only_shared(self):
        ids = set(services.get_portfolios_for_user(self.editor).values_list("id", flat=True))
        self.assertEqual(ids, {self.shared.id})

    def test_viewer_sees_only_shared(self):
        ids = set(services.get_portfolios_for_user(self.viewer).values_list("id", flat=True))
        self.assertEqual(ids, {self.shared.id})

    def test_stranger_sees_nothing(self):
        self.assertEqual(list(services.get_portfolios_for_user(self.stranger)), [])

    def test_anonymous_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertEqual(list(services.get_portfolios_for_user(AnonymousUser())), [])


class GetPortfolioForUserTests(ServiceIsolationBase):
    def test_member_gets_portfolio(self):
        self.assertEqual(
            services.get_portfolio_for_user(self.viewer, self.shared.id).id,
            self.shared.id,
        )

    def test_non_member_gets_none(self):
        self.assertIsNone(services.get_portfolio_for_user(self.viewer, self.hidden.id))

    def test_anonymous_gets_none(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(services.get_portfolio_for_user(AnonymousUser(), self.shared.id))

    def test_bad_id_gets_none(self):
        self.assertIsNone(services.get_portfolio_for_user(self.viewer, "not-an-int"))
        self.assertIsNone(services.get_portfolio_for_user(self.viewer, 999999))


class GetAssetsForUserTests(ServiceIsolationBase):
    def test_member_sees_assets(self):
        ids = set(services.get_assets_for_user(self.viewer, self.shared.id).values_list("id", flat=True))
        self.assertEqual(ids, {self.shared_asset.id})

    def test_non_member_sees_nothing(self):
        self.assertEqual(list(services.get_assets_for_user(self.viewer, self.hidden.id)), [])


class GetTransactionsForUserTests(ServiceIsolationBase):
    def test_member_sees_transactions(self):
        ids = set(
            services.get_transactions_for_user(self.viewer, self.shared.id)
            .values_list("id", flat=True)
        )
        self.assertEqual(ids, {self.shared_tx.id})

    def test_non_member_sees_nothing(self):
        self.assertEqual(
            list(services.get_transactions_for_user(self.viewer, self.hidden.id)),
            [],
        )


class UserRoleOnPortfolioTests(ServiceIsolationBase):
    def test_roles(self):
        self.assertEqual(services.user_role_on_portfolio(self.owner, self.shared.id), "OWNER")
        self.assertEqual(services.user_role_on_portfolio(self.editor, self.shared.id), "EDITOR")
        self.assertEqual(services.user_role_on_portfolio(self.viewer, self.shared.id), "VIEWER")

    def test_non_member_is_none(self):
        self.assertIsNone(services.user_role_on_portfolio(self.viewer, self.hidden.id))

    def test_anonymous_is_none(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(services.user_role_on_portfolio(AnonymousUser(), self.shared.id))
