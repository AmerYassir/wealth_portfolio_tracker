"""The ONLY data-access path for portfolio / asset / transaction / membership data.

Every function here takes `user` first and filters by membership internally.
Returns an empty queryset (or None) when the user has no access — never raises
a leak. DRF views and agent tools both call these; neither may build its own
queryset for portfolio-scoped data.

Contract (Phase 2):
- The user is always the first positional argument, always a User instance
  (anonymous is not handled here — views enforce authentication before
  calling into this module).
- No function raises because of permission denial. Not-found and not-a-member
  are indistinguishable to callers on purpose: no leakage by exception type.
- Functions return live QuerySets where possible, so callers can add their own
  .order_by() / .filter() for presentation — but only presentation. All
  *security* filtering lives here.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import QuerySet

from .models import Asset, Membership, Portfolio, Transaction


def _user_is_authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _membership_qs_for(user) -> QuerySet:
    """Memberships for this user. Empty queryset for anonymous."""
    if not _user_is_authenticated(user):
        return Membership.objects.none()
    return Membership.objects.filter(user=user)


def get_portfolios_for_user(user) -> QuerySet:
    """Portfolios `user` is a member of. Empty queryset if anonymous or none."""
    if not _user_is_authenticated(user):
        return Portfolio.objects.none()
    return (
        Portfolio.objects.filter(memberships__user=user)
        .distinct()
        .order_by("id")
    )


def get_portfolio_for_user(user, portfolio_id: int) -> Optional[Portfolio]:
    """Portfolio if user is a member, else None. Collapses 404 and 403."""
    if not _user_is_authenticated(user):
        return None
    try:
        pid = int(portfolio_id)
    except (TypeError, ValueError):
        return None
    return (
        Portfolio.objects.filter(memberships__user=user, pk=pid)
        .distinct()
        .first()
    )


def get_assets_for_user(user, portfolio_id: int) -> QuerySet:
    """Assets of `portfolio_id` if user is a member, else empty."""
    if get_portfolio_for_user(user, portfolio_id) is None:
        return Asset.objects.none()
    return Asset.objects.filter(portfolio_id=int(portfolio_id)).order_by("id")


def get_transactions_for_user(
    user,
    portfolio_id: int,
    date_from=None,
    date_to=None,
) -> QuerySet:
    """Transactions of `portfolio_id` if user is a member, else empty.

    Optional date window on Transaction.occurred_at (inclusive). Callers pass
    timezone-aware datetimes. Naive input is treated as UTC by Django because
    USE_TZ=True.
    """
    if get_portfolio_for_user(user, portfolio_id) is None:
        return Transaction.objects.none()

    qs = Transaction.objects.filter(asset__portfolio_id=int(portfolio_id))
    if date_from is not None:
        qs = qs.filter(occurred_at__gte=date_from)
    if date_to is not None:
        qs = qs.filter(occurred_at__lte=date_to)
    return qs.order_by("-occurred_at", "-id")


def user_role_on_portfolio(user, portfolio_id: int) -> Optional[str]:
    """'OWNER' | 'EDITOR' | 'VIEWER' | None. None if not a member or anonymous."""
    if not _user_is_authenticated(user):
        return None
    try:
        pid = int(portfolio_id)
    except (TypeError, ValueError):
        return None
    return (
        Membership.objects.filter(user=user, portfolio_id=pid)
        .values_list("role", flat=True)
        .first()
    )

def log_transaction(
    user,
    portfolio_id: int,
    asset_id: int,
    tx_type: str,
    amount,
    occurred_at,
):
    """Log a transaction on a portfolio the user can write to.

    Returns the created Transaction, or None if the user lacks write access
    or the asset does not belong to the portfolio. Never raises on permission
    denial — matches the contract of every other function in this module.
    """
    role = user_role_on_portfolio(user, portfolio_id)
    if role not in ("OWNER", "EDITOR"):
        return None

    portfolio = get_portfolio_for_user(user, portfolio_id)
    if portfolio is None:
        return None

    try:
        asset = Asset.objects.get(pk=asset_id, portfolio=portfolio)
    except Asset.DoesNotExist:
        return None

    return Transaction.objects.create(
        asset=asset,
        type=tx_type,
        amount=amount,
        occurred_at=occurred_at,
    )

def add_asset(user, portfolio_id: int, asset_type: str, symbol: str, quantity, cost_basis):
    """Create an asset in a portfolio the user can write to.

    Returns the created Asset, or None if the user lacks write access.
    Never raises on permission denial.
    """
    role = user_role_on_portfolio(user, portfolio_id)
    if role not in ("OWNER", "EDITOR"):
        return None

    portfolio = get_portfolio_for_user(user, portfolio_id)
    if portfolio is None:
        return None

    return Asset.objects.create(
        portfolio=portfolio,
        type=asset_type,
        symbol=symbol,
        quantity=quantity,
        cost_basis=cost_basis,
    )