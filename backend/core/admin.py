"""Admin registration. Read-mostly views for inspecting seeded data.

Not a substitute for the service layer or the API; used only to eyeball
migrations and seed output during Phase 1 review.
"""
from django.contrib import admin

from .models import Asset, Membership, Portfolio, Transaction


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = []


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_by", "created_at")
    search_fields = ("name",)
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "portfolio", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "portfolio__name")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio", "type", "symbol", "quantity", "cost_basis")
    list_filter = ("type",)
    search_fields = ("symbol", "portfolio__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "asset", "type", "amount", "occurred_at")
    list_filter = ("type",)
    search_fields = ("asset__symbol", "asset__portfolio__name")
    date_hierarchy = "occurred_at"
