from rest_framework.permissions import BasePermission


class RBACPermission(BasePermission):
    required_permission = ""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        permission = getattr(view, "required_permission", self.required_permission)
        if not permission:
            return True
        return request.user.has_perm(permission)
