"""API URL conf, mounted at /api/v1/ from config/urls.py.

Routes are strictly nested. Assets, transactions, and members have no
top-level route — cross-portfolio ID lookups are structurally impossible.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .membership_views import MembershipDetailView, MembershipListCreateView
from .views import AssetViewSet, PortfolioViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r"portfolios", PortfolioViewSet, basename="portfolio")

urlpatterns = list(router.urls)

urlpatterns += [
    path(
        "portfolios/<int:portfolio_pk>/assets/",
        AssetViewSet.as_view({"get": "list", "post": "create"}),
        name="portfolio-assets",
    ),
    path(
        "portfolios/<int:portfolio_pk>/assets/<int:pk>/",
        AssetViewSet.as_view({"get": "retrieve", "patch": "partial_update", "put": "update", "delete": "destroy"}),
        name="portfolio-asset-detail",
    ),
    path(
        "portfolios/<int:portfolio_pk>/transactions/",
        TransactionViewSet.as_view({"get": "list", "post": "create"}),
        name="portfolio-transactions",
    ),
    path(
        "portfolios/<int:portfolio_pk>/transactions/<int:pk>/",
        TransactionViewSet.as_view({"get": "retrieve", "patch": "partial_update", "put": "update", "delete": "destroy"}),
        name="portfolio-transaction-detail",
    ),
    path(
        "portfolios/<int:portfolio_pk>/members/",
        MembershipListCreateView.as_view(),
        name="portfolio-members",
    ),
    path(
        "portfolios/<int:portfolio_pk>/members/<int:pk>/",
        MembershipDetailView.as_view(),
        name="portfolio-member-detail",
    ),
]
