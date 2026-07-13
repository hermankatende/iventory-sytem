from django.db import models
from django.utils import timezone


ACTION_CHOICES = (
    ("CREATE", "CREATE"),
    ("UPDATE", "UPDATE"),
    ("DELETE", "DELETE"),
)


class AuditLog(models.Model):
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    table_name = models.CharField(max_length=128, blank=True)
    record_id = models.CharField(max_length=64, blank=True)
    reason = models.TextField(blank=True)
    date_time = models.DateTimeField(default=timezone.now)
    action_type = models.CharField(max_length=16, choices=ACTION_CHOICES, default="UPDATE")
    event_metadata = models.JSONField(default=dict)

    # Legacy fields kept for backward compatibility.
    actor = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["table_name", "record_id", "date_time"]),
        ]


class NotificationQueue(models.Model):
    channel = models.CharField(max_length=50)
    recipient = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=32, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
