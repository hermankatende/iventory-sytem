from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.application.dashboard.services.dashboard_service import DashboardService
from src.shared.utils.site_context import is_admin_user
from src.shared.utils.site_context import site_scope_from_request


dashboard_service = DashboardService()


@login_required
def dashboard(request):
    activity_page = request.GET.get("activity_page", 1)
    login_page = request.GET.get("login_page", 1)
    scope = site_scope_from_request(request)
    payload = dashboard_service.dashboard_payload(
        activity_page=activity_page,
        login_page=login_page,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
        include_security_feed=is_admin_user(request.user),
    )

    breadcrumbs = [
        {"label": "Home", "url": "#"},
        {"label": "Dashboard", "url": ""},
    ]

    return render(
        request,
        "dashboard.html",
        {
            "cards": payload["cards"],
            "charts": payload["charts"],
            "activity_page_obj": payload["activity_page_obj"],
            "login_page_obj": payload["login_page_obj"],
            "breadcrumbs": breadcrumbs,
        },
    )
