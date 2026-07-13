from django.contrib import admin
from django.urls import include, path

from src.presentation.web.views.site_context_views import switch_active_site_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.authentication.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("", include("apps.purchases.urls")),
    path("reports/", include("apps.reports.urls")),
    path("context/switch-site/", switch_active_site_view, name="switch_active_site"),
    path("", include("apps.users.urls")),
    path("api/v1/", include("src.presentation.api.v1.urls")),
]
