"""Domain models: Portfolio, Membership, Asset, Transaction.

Field notes:
- Role / type enums are TextChoices (VARCHAR columns), not DB enums, so adding
  a value later is a code-only change.
- Money and quantities use Decimal(20, 8) to cover fiat + crypto without
  loss-of-precision surprises. Never FloatField.
- Asset.quantity and Asset.cost_basis are denormalized display snapshots.
  Nothing in Phases 1-5 recomputes them from transactions.
"""
from django.conf import settings
from django.db import models


class Portfolio(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="portfolios_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["created_by"])]

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        EDITOR = "EDITOR", "Editor"
        VIEWER = "VIEWER", "Viewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=8, choices=Role.choices)

    class Meta:
        unique_together = [("user", "portfolio")]
        indexes = [
            models.Index(fields=["user", "portfolio"]),
            models.Index(fields=["portfolio", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} / {self.portfolio} ({self.role})"


class Asset(models.Model):
    class Type(models.TextChoices):
        STOCK = "STOCK", "Stock"
        CRYPTO = "CRYPTO", "Crypto"
        REAL_ESTATE = "REAL_ESTATE", "Real estate"
        CASH = "CASH", "Cash"

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    type = models.CharField(max_length=16, choices=Type.choices)
    symbol = models.CharField(max_length=32)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    cost_basis = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["portfolio", "type"]),
            models.Index(fields=["portfolio", "symbol"]),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} ({self.type})"


class Transaction(models.Model):
    class Type(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"
        DIVIDEND = "DIVIDEND", "Dividend"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    type = models.CharField(max_length=8, choices=Type.choices)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["asset", "-occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} {self.amount} @ {self.occurred_at:%Y-%m-%d}"
