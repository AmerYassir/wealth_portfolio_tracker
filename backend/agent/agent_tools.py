"""Agent tool registry.

Tools are plain callables — the @tool decorator derives JSON Schema from the
signature. No tool accepts `user_id`; identity is established by get_user()
in agent/urls.py and read here via a ContextVar.

Every tool calls core.services. No direct ORM access for portfolio data.
"""
import contextvars
from datetime import datetime

from django_ag_ui import ToolRegistry, tool

from core import services

_current_user = contextvars.ContextVar("current_user", default=None)


def set_current_user(user):
    """Called by get_user() before the agent runs."""
    _current_user.set(user)


def _user():
    u = _current_user.get()
    if u is None or not getattr(u, "is_authenticated", False):
        raise PermissionError("no authenticated user")
    return u


registry = ToolRegistry()


@tool(registry, summary="List my portfolios")
def list_my_portfolios() -> list[dict]:
    """List the portfolios the current user is a member of."""
    user = _user()
    return [
        {
            "id": p.id,
            "name": p.name,
            "role": services.user_role_on_portfolio(user, p.id),
        }
        for p in services.get_portfolios_for_user(user)
    ]


@tool(registry, summary="Get portfolio summary")
def get_portfolio_summary(portfolio_id: int) -> dict:
    """Summarize a portfolio: name, role, asset count, total cost basis,
    asset breakdown by type.

    Returns {"error": "not found or access denied"} if the user is not a
    member — the same phrasing the spec requires.
    """
    user = _user()
    portfolio = services.get_portfolio_for_user(user, portfolio_id)
    if portfolio is None:
        return {"error": "not found or access denied"}

    assets = list(services.get_assets_for_user(user, portfolio_id))
    by_type: dict[str, int] = {}
    total_cost = 0
    for a in assets:
        by_type[a.type] = by_type.get(a.type, 0) + 1
        total_cost += a.cost_basis

    return {
    "id": portfolio.id,
    "name": portfolio.name,
    "role": services.user_role_on_portfolio(user, portfolio_id),
    "asset_count": len(assets),
    "total_cost_basis": str(total_cost),
    "assets_by_type": by_type,
    "assets": [
        {
            "id": a.id,
            "symbol": a.symbol,
            "type": a.type,
            "quantity": str(a.quantity),
            "cost_basis": str(a.cost_basis),
        }
        for a in assets
    ],
    }


@tool(registry, summary="Query transactions")
def query_transactions(
    portfolio_id: int,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict] | dict:
    """List transactions in a portfolio, optionally within a date window.

    date_from / date_to are ISO date or datetime strings. Inclusive both ends.
    Returns {"error": "not found or access denied"} if not a member.
    """
    user = _user()
    portfolio = services.get_portfolio_for_user(user, portfolio_id)
    if portfolio is None:
        return {"error": "not found or access denied"}

    def _parse(value: str | None):
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    try:
        df = _parse(date_from)
        dt = _parse(date_to)
    except ValueError:
        return {"error": "invalid date; use ISO 8601"}

    txs = services.get_transactions_for_user(
        user, portfolio_id, date_from=df, date_to=dt
    )
    return [
        {
            "id": t.id,
            "asset_symbol": t.asset.symbol,
            "type": t.type,
            "amount": str(t.amount),
            "occurred_at": t.occurred_at.isoformat(),
        }
        for t in txs
    ]

@tool(
    registry,
    summary="Log a transaction",
    destructive=True,
    confirm="Log this transaction?",
)
def log_transaction(
    portfolio_id: int,
    asset_id: int,
    tx_type: str,
    amount: str,
    occurred_at: str,
) -> dict:
    """Log a buy, sell, or dividend on a portfolio.

    Only Editors and Owners can log transactions. Viewers get
    {"error": "not found or access denied"}.

    tx_type: "BUY", "SELL", or "DIVIDEND".
    amount: decimal string, e.g. "500.00".
    occurred_at: ISO date or datetime, e.g. "2024-01-15" or "2024-01-15T10:00:00Z".
    """
    from datetime import datetime
    from decimal import Decimal, InvalidOperation

    user = _user()

    try:
        parsed_amount = Decimal(amount)
    except (InvalidOperation, TypeError):
        return {"error": "invalid amount"}

    try:
        parsed_dt = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {"error": "invalid occurred_at; use ISO 8601"}

    if tx_type not in ("BUY", "SELL", "DIVIDEND"):
        return {"error": "invalid tx_type; use BUY, SELL, or DIVIDEND"}

    txn = services.log_transaction(
        user, portfolio_id, asset_id, tx_type, parsed_amount, parsed_dt
    )
    if txn is None:
        return {"error": "not found or access denied"}

    return {
        "id": txn.id,
        "asset_id": txn.asset_id,
        "type": txn.type,
        "amount": str(txn.amount),
        "occurred_at": txn.occurred_at.isoformat(),
    }

@tool(
    registry,
    summary="Add an asset",
    destructive=False,
    confirm="Add this asset to the portfolio?",
)
def add_asset(
    portfolio_id: int,
    asset_type: str,
    symbol: str,
    quantity: str,
    cost_basis: str,
) -> dict:
    """Add a new asset (stock, crypto, real estate, or cash) to a portfolio.

    Only Editors and Owners can add assets. Viewers get
    {"error": "not found or access denied"}.

    asset_type: "STOCK", "CRYPTO", "REAL_ESTATE", or "CASH".
    symbol: short ticker or label, e.g. "AAPL", "BTC", "HOME", "USD".
    quantity: decimal string, e.g. "10".
    cost_basis: decimal string, e.g. "1000.00".
    """
    from decimal import Decimal, InvalidOperation

    user = _user()

    if asset_type not in ("STOCK", "CRYPTO", "REAL_ESTATE", "CASH"):
        return {"error": "invalid asset_type"}
    if not symbol or not symbol.strip():
        return {"error": "symbol is required"}

    try:
        qty = Decimal(quantity)
        cost = Decimal(cost_basis)
    except (InvalidOperation, TypeError):
        return {"error": "invalid quantity or cost_basis"}

    asset = services.add_asset(
        user, portfolio_id, asset_type, symbol.strip().upper(), qty, cost
    )
    if asset is None:
        return {"error": "not found or access denied"}

    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "type": asset.type,
        "quantity": str(asset.quantity),
        "cost_basis": str(asset.cost_basis),
    }