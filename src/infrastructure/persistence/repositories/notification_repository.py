from src.application.common.interfaces.repositories import NotificationRepository
from src.infrastructure.persistence.models import NotificationQueue


class DjangoNotificationRepository(NotificationRepository):
    def enqueue(self, channel: str, recipient: str, message: str) -> None:
        NotificationQueue.objects.create(channel=channel, recipient=recipient, message=message)
