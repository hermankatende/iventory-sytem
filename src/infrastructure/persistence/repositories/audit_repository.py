from src.application.common.interfaces.repositories import AuditRepository
from src.infrastructure.persistence.models import AuditLog


class DjangoAuditRepository(AuditRepository):
    def save(self, actor: str, action: str, metadata: dict) -> None:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            metadata=metadata,
            action_type="UPDATE",
            event_metadata=metadata,
            table_name=(metadata or {}).get("table_name", ""),
            record_id=str((metadata or {}).get("record_id", "")),
            reason=(metadata or {}).get("reason", ""),
        )
