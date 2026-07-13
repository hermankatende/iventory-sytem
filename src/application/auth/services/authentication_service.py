from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from src.infrastructure.persistence.models import LoginHistory, UserSecurityProfile
from src.application.auth.services.security_service import SecurityService


class AuthenticationService:
    ROLE_PERMISSION_MAP = {
        "Admin": [
            ("add_item", "persistence"),
            ("change_item", "persistence"),
            ("delete_item", "persistence"),
            ("view_item", "persistence"),
            ("add_receipt", "persistence"),
            ("change_receipt", "persistence"),
            ("delete_receipt", "persistence"),
            ("view_receipt", "persistence"),
            ("add_expense", "persistence"),
            ("change_expense", "persistence"),
            ("delete_expense", "persistence"),
            ("view_expense", "persistence"),
            ("add_invoice", "persistence"),
            ("change_invoice", "persistence"),
            ("delete_invoice", "persistence"),
            ("view_invoice", "persistence"),
            ("add_payment", "persistence"),
            ("change_payment", "persistence"),
            ("delete_payment", "persistence"),
            ("view_payment", "persistence"),
            ("view_auditlog", "persistence"),
            ("view_user", "auth"),
            ("add_user", "auth"),
            ("change_user", "auth"),
            ("delete_user", "auth"),
        ],
        "ProjectManager": [
            ("add_receipt", "persistence"),
            ("change_receipt", "persistence"),
            ("view_receipt", "persistence"),
            ("add_invoice", "persistence"),
            ("change_invoice", "persistence"),
            ("view_invoice", "persistence"),
            ("add_expense", "persistence"),
            ("change_expense", "persistence"),
            ("view_expense", "persistence"),
            ("add_payment", "persistence"),
            ("view_payment", "persistence"),
            ("view_auditlog", "persistence"),
        ],
        "Accountant": [
            ("view_receipt", "persistence"),
            ("view_invoice", "persistence"),
            ("view_expense", "persistence"),
            ("view_payment", "persistence"),
            ("view_supplier", "persistence"),
            ("view_auditlog", "persistence"),
        ],
        "SiteEngineer": [
            ("view_receipt", "persistence"),
            ("view_invoice", "persistence"),
            ("view_expense", "persistence"),
            ("view_payment", "persistence"),
            ("view_item", "persistence"),
            ("view_stocklevel", "persistence"),
            ("view_stockmovement", "persistence"),
        ],
    }

    def _client_ip(self, request) -> str | None:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _record_login_history(self, *, username: str, user, request, was_successful: bool, failure_reason: str = "") -> None:
        LoginHistory.objects.create(
            user=user,
            username=username,
            login_time=timezone.now(),
            ip_address=self._client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
            was_successful=was_successful,
            failure_reason=failure_reason,
        )

    def _profile(self, user: User) -> UserSecurityProfile:
        profile, _ = UserSecurityProfile.objects.get_or_create(
            user=user,
            defaults={
                "inactivity_days_limit": int(getattr(settings, "ACCOUNT_INACTIVITY_DAYS", 90)),
                "max_failed_attempts": int(getattr(settings, "ACCOUNT_LOCKOUT_THRESHOLD", 5)),
                "lockout_minutes": int(getattr(settings, "ACCOUNT_LOCKOUT_MINUTES", 30)),
            },
        )
        return profile

    def _is_inactive_account(self, user: User, profile: UserSecurityProfile) -> bool:
        if user.last_login is None:
            return False
        inactivity_limit = timedelta(days=profile.inactivity_days_limit)
        return timezone.now() - user.last_login > inactivity_limit

    @transaction.atomic
    def login(self, request, username: str, password: str):
        user_lookup = User.objects.filter(username=username).first()
        if user_lookup:
            profile = self._profile(user_lookup)
            if not user_lookup.is_active:
                self._record_login_history(
                    username=username,
                    user=user_lookup,
                    request=request,
                    was_successful=False,
                    failure_reason="Account inactive.",
                )
                return None, "Account is inactive. Contact administrator."

            if profile.is_locked:
                self._record_login_history(
                    username=username,
                    user=user_lookup,
                    request=request,
                    was_successful=False,
                    failure_reason="Account is temporarily locked.",
                )
                return None, "Account is locked. Try again later."

            if self._is_inactive_account(user_lookup, profile):
                user_lookup.is_active = False
                user_lookup.save(update_fields=["is_active"])
                self._record_login_history(
                    username=username,
                    user=user_lookup,
                    request=request,
                    was_successful=False,
                    failure_reason="Inactive account.",
                )
                return None, "Account deactivated due to inactivity. Contact administrator."

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            if user_lookup:
                profile = self._profile(user_lookup)
                profile.failed_login_attempts += 1
                if profile.failed_login_attempts >= profile.max_failed_attempts:
                    profile.lock_account()
                profile.save(update_fields=["failed_login_attempts", "account_locked_until", "updated_at"])
                self._record_login_history(
                    username=username,
                    user=user_lookup,
                    request=request,
                    was_successful=False,
                    failure_reason="Invalid credentials.",
                )
            else:
                self._record_login_history(
                    username=username,
                    user=None,
                    request=request,
                    was_successful=False,
                    failure_reason="Invalid credentials.",
                )
            return None, "Invalid username or password."

        profile = self._profile(user)
        profile.failed_login_attempts = 0
        profile.account_locked_until = None
        profile.last_activity_at = timezone.now()
        profile.save(update_fields=["failed_login_attempts", "account_locked_until", "last_activity_at", "updated_at"])

        django_login(request, user)
        self._record_login_history(
            username=username,
            user=user,
            request=request,
            was_successful=True,
        )
        return user, "Login successful."

    def logout(self, request) -> None:
        django_logout(request)

    @transaction.atomic
    def register_user(self, *, username: str, password: str, role_name: str, first_name: str = "", last_name: str = "", email: str = "") -> User:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        security_service = SecurityService()
        security_service.ensure_role(user, role_name)
        for codename, app_label in self.ROLE_PERMISSION_MAP.get(role_name, []):
            security_service.grant_permission(role_name, codename, app_label)

        profile = self._profile(user)
        profile.last_activity_at = timezone.now()
        profile.save(update_fields=["last_activity_at", "updated_at"])
        security_service.record_password_change(user)
        return user
