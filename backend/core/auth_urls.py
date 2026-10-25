"""JWT auth endpoints. Mounted at /api/token/ from config/urls.py.

Separate from core/urls.py (which is mounted under /api/v1/) because auth
tokens are not versioned API surface — they're infrastructure.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
]
