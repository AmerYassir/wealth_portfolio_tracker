"""DRF ViewSets for Portfolio / Asset / Transaction.

Every queryset in this file comes from `core.services`. No `.objects.all()`,
no `.filter(portfolio=...)` written inline. That is the invariant.

Role model (see Phase 3 plan):
- Reads: any member (OWNER / EDITOR / VIEWER).
- Asset and Transaction writes: OWNER or EDITOR.
- Portfolio writes (rename / delete): OWNER only.
- `perform_create` and `perform_update` never trust the body for identity —
  `created_by` and `portfolio` come from request.user / URL kwarg.
"""
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import Portfolio
from .permissions import IsPortfolioMember
from .serializers import AssetSerializer, PortfolioSerializer, TransactionSerializer


WRITE_ROLES = {"OWNER", "EDITOR"}
OWNER_ONLY = {"OWNER"}


class _PortfolioScopedViewSet(viewsets.GenericViewSet):
    """Shared plumbing for Asset and Transaction viewsets.

    The portfolio is resolved from the URL kwarg (`portfolio_pk`) on every
    request. If the caller is not a member of that portfolio, we 404 — the
    portfolio id is disclosed by the caller, so 404 vs 403 is informational
    only, but 404 matches "not found or access denied" phrasing.
    """

    permission_classes = [IsAuthenticated]

    def _get_portfolio_or_404(self) -> Portfolio:
        portfolio = services.get_portfolio_for_user(
            self.request.user, self.kwargs.get("portfolio_pk")
        )
        if portfolio is None:
            raise PermissionDenied("Not found or access denied.")
        return portfolio

    def _require_write_role(self, portfolio) -> None:
        role = services.user_role_on_portfolio(self.request.user, portfolio.id)
        if role not in WRITE_ROLES:
            raise PermissionDenied("Write access denied.")


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return services.get_portfolios_for_user(self.request.user)

    def perform_create(self, serializer):
        # Ownership: creator becomes OWNER. Membership row is created by the
        # service layer, not here, so tests can exercise the same path as the
        # API. See services.get_portfolios_for_user — it filters on Membership.
        portfolio = serializer.save(created_by=self.request.user)
        from .models import Membership

        Membership.objects.create(
            user=self.request.user, portfolio=portfolio, role="OWNER"
        )
        return portfolio

    def _require_owner(self, portfolio):
        role = services.user_role_on_portfolio(self.request.user, portfolio.id)
        if role not in OWNER_ONLY:
            raise PermissionDenied("Only the owner can modify a portfolio.")

    def update(self, request, *args, **kwargs):
        self._require_owner(self.get_object())
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._require_owner(self.get_object())
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._require_owner(self.get_object())
        return super().destroy(request, *args, **kwargs)


class AssetViewSet(
    _PortfolioScopedViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = AssetSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # Resolve portfolio once per request so both list and detail routes
        # work without a second lookup.
        ctx["portfolio"] = self._get_portfolio_or_404()
        return ctx

    def get_queryset(self):
        portfolio = self._get_portfolio_or_404()
        return services.get_assets_for_user(self.request.user, portfolio.id)

    def perform_create(self, serializer):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        serializer.save(portfolio=portfolio)

    def perform_update(self, serializer):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        # `portfolio` is read-only on the serializer — instance.portfolio is
        # preserved. Only mutable fields change.
        serializer.save()

    def perform_destroy(self, instance):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        instance.delete()


class TransactionViewSet(
    _PortfolioScopedViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = TransactionSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["portfolio"] = self._get_portfolio_or_404()
        return ctx

    def get_queryset(self):
        portfolio = self._get_portfolio_or_404()
        # Optional ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD, validated strictly.
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        df = self._parse_date(date_from) if date_from else None
        dt = self._parse_date(date_to) if date_to else None
        return services.get_transactions_for_user(
            self.request.user, portfolio.id, date_from=df, date_to=dt
        )

    @staticmethod
    def _parse_date(value):
        from datetime import datetime

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": f"Invalid date: {value}"})

    def perform_create(self, serializer):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        serializer.save()

    def perform_update(self, serializer):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        serializer.save()

    def perform_destroy(self, instance):
        portfolio = self._get_portfolio_or_404()
        self._require_write_role(portfolio)
        instance.delete()
