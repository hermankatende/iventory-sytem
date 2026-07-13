# Design Patterns Used

- Repository Pattern: persistence abstraction for business logic isolation.
- Service Layer Pattern: use-case orchestration outside views.
- Unit of Work: transaction boundary for stock and audit consistency.
- Factory Pattern: environment-based adapter composition (offline/online).
- Strategy Pattern: selectable notification and report generation channels.
- Observer/Domain Events: decoupled audit and notifications.
- CQS: command handlers for writes, query services for reporting reads.

## SOLID Alignment
- S: each class has one responsibility.
- O: extend channels/adapters without changing use cases.
- L: repository implementations are substitutable.
- I: narrow interfaces per capability.
- D: application depends on abstractions, not Django ORM details.
