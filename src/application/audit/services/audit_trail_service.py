from src.application.common.interfaces.repositories import AuditRepository


class AuditTrailService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def record_event(self, actor: str, action: str, metadata: dict) -> None:
        self.repository.save(actor=actor, action=action, metadata=metadata)
