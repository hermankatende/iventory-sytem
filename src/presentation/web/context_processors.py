from src.shared.utils.site_context import role_flags_for_user, switchable_sites_for_user, site_scope_from_request


def site_context(request):
    if not request.user or not request.user.is_authenticated:
        return {
            "switchable_sites": [],
            "active_site_id": None,
        }

    scope = site_scope_from_request(request)
    role_flags = role_flags_for_user(request.user)
    return {
        "switchable_sites": switchable_sites_for_user(request.user),
        "active_site_id": scope["active_site_id"],
        **role_flags,
    }
