from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User

from src.application.auth.services.security_service import SecurityService


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


class SignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Accountant", "Accountant"),
        ("ProjectManager", "Project Manager"),
        ("SiteEngineer", "Site Engineer"),
    ]

    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "id": "id_password1"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "id": "id_password2"}))

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email


class PasswordChangeWithHistoryForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean_new_password1(self):
        new_password = self.cleaned_data["new_password1"]
        try:
            SecurityService().enforce_password_history(self.user, new_password)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return new_password


class EmailBasedPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
