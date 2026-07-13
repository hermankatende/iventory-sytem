from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils import timezone

from src.infrastructure.persistence.models import PasswordHistory, UserSecurityProfile


class SecurityService:
    def get_or_create_profile(self, user: User) -> UserSecurityProfile:
        profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
        return profile

    @transaction.atomic
    def enforce_password_history(self, user: User, raw_password: str, recent_count: int = 5) -> None:
        recent_history = PasswordHistory.objects.filter(user=user).order_by("-created_at")[:recent_count]
        for entry in recent_history:
            if check_password(raw_password, entry.password_hash):
                raise ValueError("You cannot reuse a recently used password.")

    @transaction.atomic
    def record_password_change(self, user: User) -> None:
        profile = self.get_or_create_profile(user)
        profile.password_changed_at = timezone.now()
        profile.force_password_change = False
        profile.save(update_fields=["password_changed_at", "force_password_change", "updated_at"])
        PasswordHistory.objects.create(user=user, password_hash=user.password)

    @transaction.atomic
    def ensure_role(self, user: User, role_name: str) -> None:
        role, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(role)

    @transaction.atomic
    def grant_permission(self, role_name: str, permission_codename: str, app_label: str) -> None:
        role, _ = Group.objects.get_or_create(name=role_name)
        permission = Permission.objects.get(codename=permission_codename, content_type__app_label=app_label)
        role.permissions.add(permission)
