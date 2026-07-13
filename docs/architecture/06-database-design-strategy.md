# Database Design Strategy

## Database Engine
- MySQL for transactional consistency and indexing performance.

## Core Modeling
- 3NF for transactional tables.
- Referential integrity via FK constraints.
- Composite unique constraints for business keys.

## Main Table Groups
- Identity: users, roles, permissions, user_roles.
- Inventory: items, warehouses, stock_levels, stock_movements.
- Suppliers: suppliers, contacts, ratings, supplier_item_map.
- Procurement: requisitions, purchase_orders, goods_receipts.
- Cross-cutting: audit_logs, notification_queue, backup_jobs, report_jobs.

## Performance and Integrity
- Index by lookup and reporting paths.
- Use transactions for inventory mutations.
- Apply optimistic/pessimistic lock selectively for stock contention.
- Archive large audit and movement datasets by retention policy.
