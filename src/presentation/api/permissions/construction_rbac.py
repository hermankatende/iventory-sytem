from rest_framework.permissions import BasePermission, SAFE_METHODS


class ConstructionRBACPermission(BasePermission):
    """Role-based access policy for construction ERP endpoints."""

    read_roles = {"Admin", "ProjectManager", "Accountant", "SiteEngineer"}
    write_roles = {"Admin"}
    delete_roles = {"Admin"}

    def _user_roles(self, request) -> set[str]:
        if not request.user or not request.user.is_authenticated:
            return set()
        return set(request.user.groups.values_list("name", flat=True))

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        roles = self._user_roles(request)

        view_read_roles = set(getattr(view, "read_roles", self.read_roles))
        view_write_roles = set(getattr(view, "write_roles", self.write_roles))
        view_delete_roles = set(getattr(view, "delete_roles", self.delete_roles))

        if request.method in SAFE_METHODS:
            return bool(roles & view_read_roles)

        if request.method == "DELETE":
            return bool(roles & view_delete_roles)

        return bool(roles & view_write_roles)
