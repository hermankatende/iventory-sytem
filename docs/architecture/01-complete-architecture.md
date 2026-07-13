# Complete Architecture

## Architectural Style
- Clean Architecture using a modular monolith deployment model.
- Offline-first runtime with local MySQL and local storage.
- Online deployment later by changing infrastructure configuration only.

## Layers
- Presentation Layer: Django templates, Bootstrap 5, JavaScript, DRF endpoints.
- Business Logic Layer: service classes and use cases in `src/application`.
- Repository Layer: interfaces in application, implementations in infrastructure.
- Data Layer: Django ORM models and MySQL schema.

## Core Cross-Cutting Services
- Authentication and Authorization using Django auth + role/permission mapping.
- Logging with structured rotating logs.
- Exception Handling through middleware and DRF exception handler.
- Audit Trail for state-changing API operations.
- Backup/Restore services for offline resiliency.
- Report service for inventory and procurement analytics.
- Notification service with local queue backend.

## Offline-First to Online Transition
- Keep domain and application services unchanged.
- Replace infrastructure adapters through settings and dependency injection.
- Move from local filesystem/logging/queue to managed cloud services when needed.
