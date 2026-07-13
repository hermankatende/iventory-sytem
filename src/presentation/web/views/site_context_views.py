from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from src.shared.utils.site_context import assigned_site_ids_for_user, set_active_site_id


@login_required
@require_http_methods(["POST"])
def switch_active_site_view(request):
    raw_site_id = request.POST.get("site_id", "")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    if not raw_site_id:
        set_active_site_id(request, None)
        return redirect(next_url)

    try:
        site_id = int(raw_site_id)
    except (TypeError, ValueError):
        return redirect(next_url)

    assigned_ids = assigned_site_ids_for_user(request.user)
    if assigned_ids is None or site_id in assigned_ids:
        set_active_site_id(request, site_id)

    return redirect(next_url)
