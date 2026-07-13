from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            timeout_seconds = int(getattr(settings, "SESSION_COOKIE_AGE", 1800))
            last_activity_ts = request.session.get("last_activity_ts")
            now_ts = int(timezone.now().timestamp())

            if last_activity_ts and (now_ts - int(last_activity_ts)) > timeout_seconds:
                logout(request)
                messages.warning(request, "Session expired due to inactivity. Please sign in again.")
                return redirect("login")

            request.session["last_activity_ts"] = now_ts

        return self.get_response(request)
