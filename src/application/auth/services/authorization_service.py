class AuthorizationService:
    def has_permission(self, user, permission_codename: str) -> bool:
        if not user or not user.is_authenticated:
            return False
        return user.has_perm(permission_codename)

    def has_role(self, user, role_name: str) -> bool:
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name=role_name).exists()

    def require_all_permissions(self, user, permission_codenames: list[str]) -> bool:
        if not user or not user.is_authenticated:
            return False
        return all(user.has_perm(code) for code in permission_codenames)
