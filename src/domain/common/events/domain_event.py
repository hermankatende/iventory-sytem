from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DomainEvent:
    event_name: str
    occurred_at: datetime
    payload: dict
