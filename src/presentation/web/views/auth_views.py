from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from src.application.auth.services.authentication_service import AuthenticationService
from src.application.auth.services.security_service import SecurityService
from src.infrastructure.persistence.models import LoginHistory, UserActivityLog
from src.presentation.web.forms.auth_forms import EmailBasedPasswordResetForm, LoginForm, PasswordChangeWithHistoryForm, SignupForm
from src.presentation.web.permissions import require_role


authentication_service = AuthenticationService()
security_service = SecurityService()


class LoginView(View):
    template_name = "auth/login.html"
    form_class = LoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request):
        form = self.form_class(request=request, data=request.POST)
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user, message = authentication_service.login(request, username=username, password=password)
        if user is None:
            messages.error(request, message)
            if not form.is_valid():
                form.add_error(None, "Enter a valid username and password.")
            return render(request, self.template_name, {"form": form})

        messages.success(request, message)
        return redirect("dashboard")


class SignupView(View):
    template_name = "auth/signup.html"
    form_class = SignupForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        data = form.cleaned_data
        authentication_service.register_user(
            username=data["username"],
            password=data["password1"],
            role_name=data["role"],
            first_name="",
            last_name="",
            email=data.get("email", ""),
        )
        user, message = authentication_service.login(request, data["username"], data["password1"])
        if user is None:
            messages.success(request, "Account created successfully. Please sign in.")
            return redirect("login")

        messages.success(request, f"{message} Your account has been created.")
        return redirect("dashboard")


@login_required
def logout_view(request):
    authentication_service.logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@method_decorator(login_required, name="dispatch")
class PasswordChangeView(View):
    template_name = "auth/password_change.html"
    form_class = PasswordChangeWithHistoryForm

    def get(self, request):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(user=request.user, data=request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = form.save()
        update_session_auth_hash(request, user)
        security_service.record_password_change(user)
        messages.success(request, "Password changed successfully.")
        return redirect("dashboard")


@method_decorator(require_role("Admin"), name="dispatch")
class LoginHistoryView(ListView):
    template_name = "auth/login_history.html"
    context_object_name = "entries"

    def get_queryset(self):
        return LoginHistory.objects.select_related("user").order_by("-created_at")[:200]


@method_decorator(require_role("Admin"), name="dispatch")
class SecurityActivityView(ListView):
    template_name = "auth/security_activity.html"
    context_object_name = "entries"

    def get_queryset(self):
        return UserActivityLog.objects.select_related("user").order_by("-created_at")[:200]


@method_decorator(require_role("Admin"), name="dispatch")
class UserManagementView(ListView):
    template_name = "auth/user_management.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.prefetch_related("groups").order_by("username")


@require_role("Admin")
def delete_user_view(request, user_id: int):
    if request.method != "POST":
        return redirect("user_management")

    target = get_object_or_404(User, id=user_id)
    if target.id == request.user.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect("user_management")

    username = target.username
    target.delete()
    messages.success(request, f"User {username} deleted successfully.")
    return redirect("user_management")


class ForgotPasswordView(PasswordResetView):
    template_name = "auth/password_reset_form.html"
    form_class = EmailBasedPasswordResetForm
    email_template_name = "auth/password_reset_email.txt"
    subject_template_name = "auth/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class ForgotPasswordDoneView(PasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class ForgotPasswordConfirmView(PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class ForgotPasswordCompleteView(PasswordResetCompleteView):
    template_name = "auth/password_reset_complete.html"
