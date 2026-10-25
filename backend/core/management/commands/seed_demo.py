"""Idempotent demo seed.

Users (password: pass1234):
  owner   - member of Shared Household (OWNER), Owner Only (OWNER)
  editor  - member of Shared Household (EDITOR)
  viewer  - member of Shared Household (VIEWER)

Re-running this command:
  - does not duplicate users, portfolios, memberships, assets, or transactions
  - does not reset passwords on existing users (so a manually-changed password
    survives a re-seed)
  - updates role on existing memberships only if it drifted
"""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Asset, Membership, Portfolio, Transaction

PASSWORD = "pass1234"

USERS = [
    ("owner", "owner@example.test", "Ophelia Owner"),
    ("editor", "editor@example.test", "Eddie Editor"),
    ("viewer", "viewer@example.test", "Vera Viewer"),
]

# name -> {username: role}
PORTFOLIOS = {
    "Shared Household": {"owner": "OWNER", "editor": "EDITOR", "viewer": "VIEWER"},
    "Owner Only": {"owner": "OWNER"},
}

# portfolio name -> list of (asset type, symbol, quantity, cost_basis)
ASSETS = {
    "Shared Household": [
        ("STOCK", "AAPL", Decimal("50"), Decimal("7500")),
        ("STOCK", "VTI", Decimal("100"), Decimal("22000")),
        ("CRYPTO", "BTC", Decimal("0.25"), Decimal("8000")),
        ("REAL_ESTATE", "HOME", Decimal("1"), Decimal("350000")),
        ("CASH", "USD", Decimal("25000"), Decimal("25000")),
    ],
    "Owner Only": [
        ("STOCK", "TSLA", Decimal("10"), Decimal("2500")),
        ("CASH", "USD", Decimal("5000"), Decimal("5000")),
    ],
}

# (portfolio, symbol, type, amount, iso datetime)
TRANSACTIONS = [
    ("Shared Household", "AAPL", "BUY", Decimal("50"), "2023-04-01T10:00:00Z"),
    ("Shared Household", "AAPL", "DIVIDEND", Decimal("12.50"), "2024-01-15T10:00:00Z"),
    ("Shared Household", "VTI", "BUY", Decimal("100"), "2023-06-01T10:00:00Z"),
    ("Shared Household", "VTI", "DIVIDEND", Decimal("150"), "2024-03-15T10:00:00Z"),
    ("Shared Household", "BTC", "BUY", Decimal("0.25"), "2023-11-20T14:30:00Z"),
    ("Shared Household", "HOME", "BUY", Decimal("1"), "2020-01-15T09:00:00Z"),
    ("Shared Household", "USD", "BUY", Decimal("25000"), "2024-04-01T08:00:00Z"),
    ("Owner Only", "TSLA", "BUY", Decimal("10"), "2024-02-10T11:00:00Z"),
    ("Owner Only", "USD", "BUY", Decimal("5000"), "2024-05-01T08:00:00Z"),
]


def _parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(dt_timezone.utc)


class Command(BaseCommand):
    help = "Seed demo users, portfolios, memberships, assets, and transactions (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # --- users ---
        users: dict[str, "User"] = {}
        for username, email, full_name in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "first_name": full_name.split()[0]},
            )
            if created:
                user.set_password(PASSWORD)
                user.save(update_fields=["password"])
                self.stdout.write(self.style.SUCCESS(f"created user {username}"))
            else:
                self.stdout.write(f"user {username} already exists")
            users[username] = user

        # --- portfolios + memberships ---
        portfolios: dict[str, Portfolio] = {}
        for name, roles in PORTFOLIOS.items():
            owner = users[next(iter(roles))]
            portfolio, created = Portfolio.objects.get_or_create(
                name=name,
                defaults={"created_by": owner},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"created portfolio {name}"))
            else:
                self.stdout.write(f"portfolio {name} already exists")
            portfolios[name] = portfolio

            for username, role in roles.items():
                membership, m_created = Membership.objects.get_or_create(
                    user=users[username],
                    portfolio=portfolio,
                    defaults={"role": role},
                )
                if m_created:
                    self.stdout.write(f"  + membership {username}={role}")
                elif membership.role != role:
                    membership.role = role
                    membership.save(update_fields=["role"])
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ~ membership {username} role updated to {role}"
                        )
                    )

        # --- assets ---
        for portfolio_name, rows in ASSETS.items():
            portfolio = portfolios[portfolio_name]
            for asset_type, symbol, qty, cost in rows:
                asset, created = Asset.objects.get_or_create(
                    portfolio=portfolio,
                    symbol=symbol,
                    defaults={"type": asset_type, "quantity": qty, "cost_basis": cost},
                )
                if created:
                    self.stdout.write(f"  + asset {symbol} in {portfolio_name}")
                else:
                    self.stdout.write(f"  asset {symbol} in {portfolio_name} exists")

        # --- transactions ---
        # Natural key: (asset, type, amount, occurred_at). No duplicates on re-run.
        for portfolio_name, symbol, tx_type, amount, iso in TRANSACTIONS:
            asset = Asset.objects.get(portfolio=portfolios[portfolio_name], symbol=symbol)
            occurred_at = _parse_dt(iso)
            _, created = Transaction.objects.get_or_create(
                asset=asset,
                type=tx_type,
                amount=amount,
                occurred_at=occurred_at,
            )
            if created:
                self.stdout.write(f"  + tx {tx_type} {symbol} {amount} {iso}")
            else:
                self.stdout.write(f"  tx {tx_type} {symbol} {iso} exists")

        self.stdout.write(self.style.SUCCESS("seed_demo complete"))
