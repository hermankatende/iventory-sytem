from django.urls import path

from apps.authentication.views import (
    ForgotPasswordCompleteView,
    ForgotPasswordConfirmView,
    ForgotPasswordDoneView,
    ForgotPasswordView,
    LoginHistoryView,
    LoginView,
    PasswordChangeView,
    SecurityActivityView,
    UserManagementView,
    SignupView,
    delete_user_view,
    logout_view,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", logout_view, name="logout"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="password_reset"),
    path("forgot-password/done/", ForgotPasswordDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", ForgotPasswordConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/complete/", ForgotPasswordCompleteView.as_view(), name="password_reset_complete"),
    path("login-history/", LoginHistoryView.as_view(), name="login_history"),
    path("security-activity/", SecurityActivityView.as_view(), name="security_activity"),
    path("users/", UserManagementView.as_view(), name="user_management"),
    path("users/<int:user_id>/delete/", delete_user_view, name="delete_user"),
]
