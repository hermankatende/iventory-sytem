from src.application.common.interfaces.repositories import NotificationRepository


class NotificationService:
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    def send(self, channel: str, recipient: str, message: str) -> None:
        self.notification_repository.enqueue(channel=channel, recipient=recipient, message=message)
