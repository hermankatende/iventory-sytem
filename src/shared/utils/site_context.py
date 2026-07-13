from __future__ import annotations

from typing import Any

from src.infrastructure.persistence.models import UserSite, Warehouse


def is_admin_user(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name="Admin").exists() or user.is_superuser


def role_names_for_user(user) -> set[str]:
    if not user or not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def role_flags_for_user(user) -> dict[str, bool]:
    roles = role_names_for_user(user)
    is_admin = is_admin_user(user)
    return {
        "is_admin": is_admin,
        "is_project_manager": "ProjectManager" in roles,
        "is_accountant": "Accountant" in roles,
        "is_site_engineer": "SiteEngineer" in roles,
        "can_view_admin_tools": is_admin,
        "can_view_reporting": is_admin or "ProjectManager" in roles or "Accountant" in roles,
        "can_view_payments": is_admin or "Accountant" in roles,
        "can_view_expenses": is_admin or "ProjectManager" in roles or "Accountant" in roles,
    }


def assigned_site_ids_for_user(user) -> list[int] | None:
    """Return allowed site IDs for a user; None means unrestricted (Admin)."""
    if not user or not user.is_authenticated:
        return []
    if is_admin_user(user):
        return None
    return list(UserSite.objects.filter(user_id=user.id).values_list("site_id", flat=True))


def switchable_sites_for_user(user):
    if not user or not user.is_authenticated:
        return Warehouse.objects.none()
    if is_admin_user(user):
        return Warehouse.objects.order_by("name")
    return Warehouse.objects.filter(id__in=UserSite.objects.filter(user_id=user.id).values_list("site_id", flat=True)).order_by("name")


def get_active_site_id(request, *, assigned_site_ids: list[int] | None) -> int | None:
    active = request.session.get("active_site_id")
    if active is None:
        return None

    try:
        active = int(active)
    except (TypeError, ValueError):
        return None

    if assigned_site_ids is None:
        return active
    return active if active in assigned_site_ids else None


def set_active_site_id(request, site_id: int | None) -> None:
    if site_id is None:
        request.session.pop("active_site_id", None)
    else:
        request.session["active_site_id"] = int(site_id)


def site_scope_from_request(request) -> dict[str, Any]:
    assigned_site_ids = assigned_site_ids_for_user(request.user)
    active_site_id = get_active_site_id(request, assigned_site_ids=assigned_site_ids)
    return {
        "assigned_site_ids": assigned_site_ids,
        "active_site_id": active_site_id,
    }


def apply_site_scope(queryset, *, field_name: str, assigned_site_ids: list[int] | None, active_site_id: int | None = None, explicit_site_id: int | None = None):
    if explicit_site_id:
        return queryset.filter(**{field_name: explicit_site_id})
    if active_site_id:
        return queryset.filter(**{field_name: active_site_id})
    if assigned_site_ids is None:
        return queryset
    if not assigned_site_ids:
        return queryset.none()
    return queryset.filter(**{f"{field_name}__in": assigned_site_ids})
