# 08 Offline-First and Future Cloud Strategy

## Runtime Modes
- Offline mode: local network deployment with private MySQL and file-based media.
- Online/cloud mode: same codebase, environment-only configuration changes.

## Non-Rewrite Migration Principle
- Keep all business rules in application services.
- Keep persistence concerns behind repository interfaces.
- Keep presentation layer independent from deployment topology.

## Offline Requirements
- No internet dependencies in critical paths.
- Local static and media hosting.
- Local logging and backup scripts.
- LAN-only DNS/IP and firewall controls.

## Cloud-Ready Controls
- Environment-based settings (`offline.py` / `online.py`).
- Stateless web workers and managed DB readiness.
- Storage abstraction for media migration (local -> cloud object storage).
- Structured logs for central aggregation in hosted environments.

## Security and Audit
- Permission gates for high-risk operations.
- Immutable receipt numbers and edit trail metadata.
- Login and activity history retained for forensics.

## Deployment Notes
- Keep `deployment/windows` and `deployment/linux` runbooks as source of truth.
- Validate every release with integration tests under `config.settings.test`.
