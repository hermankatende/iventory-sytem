"""Web permission helpers for role and permission checks."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


def _require(predicate: Callable[[Any], bool], message: str):
    """Wrap a predicate into a decorator with friendly UX on failure."""

    def decorator(view_func: Callable[..., HttpResponse]):
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            if predicate(request.user):
                return view_func(request, *args, **kwargs)
            messages.error(request, message)
            return redirect("dashboard")

        return _wrapped

    return decorator


def require_role(role_name: str):
    """Allow access only for authenticated users in the given role/group."""

    return _require(
        lambda u: bool(u and u.is_authenticated and u.groups.filter(name=role_name).exists()),
        f"You need the {role_name} role to access this page.",
    )


def require_permission(permission_codename: str):
    """Allow access only for authenticated users with the given permission."""

    return _require(
        lambda u: bool(u and u.is_authenticated and u.has_perm(permission_codename)),
        f"Missing permission: {permission_codename}",
    )
