"""API URL conf, mounted at /api/v1/ from config/urls.py.

Routes are strictly nested. Assets and transactions have no top-level route —
that is a deliberate security property, not an oversight. See Phase 3 plan.
"""
from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, PortfolioViewSet, TransactionViewSet

router = DefaultRouter()
# The bare list/create/detail routes for portfolios.
router.register(r"portfolios", PortfolioViewSet, basename="portfolio")
# Nested routes are wired manually below; the routers above only serve the
# top-level portfolio endpoints. We do NOT register assets or transactions as
# top-level resources — doing so would allow cross-portfolio ID lookups.

urlpatterns = list(router.urls)


# --- nested: /portfolios/{portfolio_pk}/assets/... --------------------------
from django.urls import path  # noqa: E402

urlpatterns += [
    path(
        "portfolios/<int:portfolio_pk>/assets/",
        AssetViewSet.as_view({"get": "list", "post": "create"}),
        name="portfolio-assets",
    ),
    path(
        "portfolios/<int:portfolio_pk>/assets/<int:pk>/",
        AssetViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "put": "update",
                "delete": "destroy",
            }
        ),
        name="portfolio-asset-detail",
    ),
    path(
        "portfolios/<int:portfolio_pk>/transactions/",
        TransactionViewSet.as_view({"get": "list", "post": "create"}),
        name="portfolio-transactions",
    ),
    path(
        "portfolios/<int:portfolio_pk>/transactions/<int:pk>/",
        TransactionViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "put": "update",
                "delete": "destroy",
            }
        ),
        name="portfolio-transaction-detail",
    ),
]
