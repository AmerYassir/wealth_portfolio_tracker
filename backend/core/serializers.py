"""DRF serializers.

Rules:
1. `created_by` is read-only, server-side identity only.
2. `portfolio` on Asset / Transaction is read-only, set from URL kwarg.
3. Transaction.asset must belong to the URL portfolio.
4. Portfolio.role is a read-only convenience for the UI (hides write controls
   for Viewer). It is NOT used for authorization — permission is enforced in
   the view layer via services.user_role_on_portfolio.
"""
from rest_framework import serializers

from . import services
from .models import Asset, Portfolio, Transaction


class PortfolioSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "name", "created_by", "created_at", "role")
        read_only_fields = ("id", "created_by", "created_at", "role")

    def get_role(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        return services.user_role_on_portfolio(request.user, obj.id)


class AssetSerializer(serializers.ModelSerializer):
    portfolio = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Asset
        fields = ("id", "portfolio", "type", "symbol", "quantity", "cost_basis")
        read_only_fields = ("id", "portfolio")


class TransactionSerializer(serializers.ModelSerializer):
    asset = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all())

    class Meta:
        model = Transaction
        fields = ("id", "asset", "type", "amount", "occurred_at")
        read_only_fields = ("id",)

    def validate(self, attrs):
        portfolio = self.context.get("portfolio")
        asset = attrs.get("asset") or getattr(self.instance, "asset", None)
        if portfolio is None:
            raise serializers.ValidationError(
                {"detail": "Serializer used without portfolio context."}
            )
        if asset is not None and asset.portfolio_id != portfolio.id:
            raise serializers.ValidationError(
                {"asset": ["Asset does not belong to this portfolio."]}
            )
        return attrs
