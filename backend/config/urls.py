"""
Root URL configuration.

API endpoints:   /api/...
Auth endpoints:  /auth/...
Admin:           /django-admin/
Everything else: served by the SPA shell (index.html)
"""

from django.contrib import admin
from django.urls import path, include
from apps.authentication.views import spa_shell

urlpatterns = [
    path("django-admin/", admin.site.urls),

    # Authentication (Cognito OAuth2 callback, login redirect, logout)
    path("auth/", include("apps.authentication.urls")),

    # REST API — all require authentication (enforced per-view via DRF)
    path("api/settings/",  include("apps.shop_settings.urls")),
    path("api/purchases/", include("apps.purchases.urls")),
    path("api/sales/",     include("apps.sales.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/finance/",   include("apps.finance.urls")),

    # SPA shell — catch-all so the React/vanilla JS router handles navigation
    path("", spa_shell, name="spa_shell"),
]
