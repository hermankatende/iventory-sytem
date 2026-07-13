# 07 Production Readiness Baseline

## Objectives
- Modular feature boundaries with explicit service and repository interfaces.
- Transaction-safe write operations for inventory, receipts, and expenses.
- Action logging and audit-ready change tracking.
- Role/permission based access controls for operational web actions.
- Test strategy covering unit and integration layers.

## Implemented Baseline
- `ReceiptService`, `InventoryService`, and `ExpenseService` use atomic transactions for write workflows.
- Web-level permission wrappers are centralized in `src/presentation/web/permissions.py`.
- Structured logger factory introduced in `src/shared/utils/app_logger.py`.
- Receipt edit trail persists field-level old/new values and editor metadata.
- Dashboard and core workflows now emit operational logs.

## Coding Standards
- PEP 8 formatting and naming.
- Type hints for new service/view helper code.
- Service/docstring coverage for business-critical modules.

## Testing Standard
- Unit tests: validators and pure rules.
- Integration tests: service + ORM workflows with DB writes.
- Test settings in `config/settings/test.py` for deterministic local execution.

Run tests:
`python manage.py test --settings=config.settings.test`

## Commit Boundaries By Feature
1. `feat(auth-hardening): permissions helpers and role guard wiring`
2. `feat(receipts): transactional service + edit trail + logs`
3. `feat(expenses): categories, service validation, reporting hooks`
4. `feat(dashboard-ui): enterprise shell and KPI charts`
5. `test(core): unit and integration baseline for receipts/expenses`
6. `docs(architecture): production readiness and deployment runbooks`
