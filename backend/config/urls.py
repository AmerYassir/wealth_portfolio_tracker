from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", include("core.auth_urls")),
    path("agent/", include("agent.urls")),
    path("api/v1/", include("core.urls")),
]