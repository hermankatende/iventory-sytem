from src.infrastructure.persistence.models import NotificationQueue


class LocalJobScheduler:
    def process_pending_notifications(self) -> int:
        pending = NotificationQueue.objects.filter(status="PENDING")[:100]
        count = 0
        for record in pending:
            record.status = "SENT"
            record.save(update_fields=["status"])
            count += 1
        return count
