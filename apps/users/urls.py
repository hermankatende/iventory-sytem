from django.urls import path

from apps.users.views import dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
]
