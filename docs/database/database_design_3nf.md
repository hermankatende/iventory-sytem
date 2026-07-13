# Construction Inventory & Supplier Management Database (3NF)

This design satisfies Third Normal Form (3NF):
- Each table models one business concept.
- Non-key attributes depend on the whole key.
- No transitive dependency on non-key attributes.
- Many-to-many relationships are resolved using junction tables.

## 1) users
Purpose: System identities for authentication and accountability.

Columns:
- user_id BIGINT UNSIGNED AI
- username VARCHAR(100) NOT NULL
- email VARCHAR(255) NOT NULL
- password_hash VARCHAR(255) NOT NULL
- first_name VARCHAR(100)
- last_name VARCHAR(100)
- is_active TINYINT(1) NOT NULL DEFAULT 1
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Primary Key:
- user_id

Foreign Keys:
- None

Indexes:
- UNIQUE(username)
- UNIQUE(email)

Constraints:
- username unique
- email unique

Relationships:
- One user to many user_roles
- One user to many receipts (created_by)
- One user to many payments (paid_by)
- One user to many expenses (created_by)
- One user to many audit_logs (actor)
- One user to many login_history
- One user to many attachments (uploaded_by)
- One user to many notifications
- One user to many settings updates

## 2) roles
Purpose: RBAC role definitions.

Columns:
- role_id BIGINT UNSIGNED AI
- role_name VARCHAR(100) NOT NULL
- role_description VARCHAR(255)
- created_at DATETIME NOT NULL

Primary Key:
- role_id

Foreign Keys:
- None

Indexes:
- UNIQUE(role_name)

Constraints:
- role_name unique

Relationships:
- One role to many user_roles
- One role to many role_permissions

## 3) permissions
Purpose: Atomic privileges used by RBAC.

Columns:
- permission_id BIGINT UNSIGNED AI
- permission_code VARCHAR(150) NOT NULL
- permission_description VARCHAR(255)
- created_at DATETIME NOT NULL

Primary Key:
- permission_id

Foreign Keys:
- None

Indexes:
- UNIQUE(permission_code)

Constraints:
- permission_code unique

Relationships:
- One permission to many role_permissions

## 4) user_roles
Purpose: Resolves many-to-many users and roles.

Columns:
- user_role_id BIGINT UNSIGNED AI
- user_id BIGINT UNSIGNED NOT NULL
- role_id BIGINT UNSIGNED NOT NULL
- assigned_at DATETIME NOT NULL
- assigned_by_user_id BIGINT UNSIGNED

Primary Key:
- user_role_id

Foreign Keys:
- user_id -> users.user_id
- role_id -> roles.role_id
- assigned_by_user_id -> users.user_id

Indexes:
- UNIQUE(user_id, role_id)
- INDEX(role_id)

Constraints:
- user-role combination unique

Relationships:
- Many user_roles rows map one user to one role

## 5) role_permissions
Purpose: Resolves many-to-many roles and permissions.

Columns:
- role_permission_id BIGINT UNSIGNED AI
- role_id BIGINT UNSIGNED NOT NULL
- permission_id BIGINT UNSIGNED NOT NULL
- granted_at DATETIME NOT NULL

Primary Key:
- role_permission_id

Foreign Keys:
- role_id -> roles.role_id
- permission_id -> permissions.permission_id

Indexes:
- UNIQUE(role_id, permission_id)
- INDEX(permission_id)

Constraints:
- role-permission combination unique

Relationships:
- Many role_permissions rows map one role to one permission

## 6) sites
Purpose: Physical locations/warehouses.

Columns:
- site_id BIGINT UNSIGNED AI
- site_code VARCHAR(50) NOT NULL
- site_name VARCHAR(200) NOT NULL
- address_line1 VARCHAR(255)
- address_line2 VARCHAR(255)
- city VARCHAR(100)
- state_region VARCHAR(100)
- country VARCHAR(100)
- postal_code VARCHAR(30)
- is_active TINYINT(1) NOT NULL DEFAULT 1
- created_at DATETIME NOT NULL

Primary Key:
- site_id

Foreign Keys:
- None

Indexes:
- UNIQUE(site_code)
- UNIQUE(site_name)

Constraints:
- unique site code and name

Relationships:
- One site to many projects
- One site to many receipts
- One site to many expenses
- One site to many inventory rows

## 7) projects
Purpose: Project master data linked to sites.

Columns:
- project_id BIGINT UNSIGNED AI
- site_id BIGINT UNSIGNED NOT NULL
- project_code VARCHAR(50) NOT NULL
- project_name VARCHAR(200) NOT NULL
- start_date DATE
- end_date DATE
- status VARCHAR(30) NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- project_id

Foreign Keys:
- site_id -> sites.site_id

Indexes:
- UNIQUE(project_code)
- INDEX(site_id)

Constraints:
- status in allowed set
- end_date >= start_date if both present

Relationships:
- Many projects belong to one site
- One project to many receipts
- One project to many expenses
- One project to many inventory transactions

## 8) suppliers
Purpose: Supplier master data.

Columns:
- supplier_id BIGINT UNSIGNED AI
- supplier_code VARCHAR(50) NOT NULL
- supplier_name VARCHAR(200) NOT NULL
- tax_number VARCHAR(100)
- email VARCHAR(255)
- phone VARCHAR(50)
- address fields
- status VARCHAR(30) NOT NULL
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Primary Key:
- supplier_id

Foreign Keys:
- None

Indexes:
- UNIQUE(supplier_code)
- UNIQUE(supplier_name)

Constraints:
- status in allowed set

Relationships:
- One supplier to many supplier_contracts
- One supplier to many price_history rows
- One supplier to many receipts
- One supplier to many invoices
- One supplier to many expenses (optional)

## 9) supplier_contracts
Purpose: Commercial agreements with suppliers.

Columns:
- contract_id BIGINT UNSIGNED AI
- supplier_id BIGINT UNSIGNED NOT NULL
- contract_number VARCHAR(100) NOT NULL
- start_date DATE NOT NULL
- end_date DATE
- payment_terms_days INT UNSIGNED NOT NULL
- status VARCHAR(30) NOT NULL
- notes VARCHAR(500)
- created_at DATETIME NOT NULL

Primary Key:
- contract_id

Foreign Keys:
- supplier_id -> suppliers.supplier_id

Indexes:
- UNIQUE(contract_number)
- INDEX(supplier_id)

Constraints:
- valid status
- end_date >= start_date when set

Relationships:
- Many contracts belong to one supplier
- One contract to many invoices

## 10) product_categories
Purpose: Product grouping taxonomy with optional hierarchy.

Columns:
- category_id BIGINT UNSIGNED AI
- parent_category_id BIGINT UNSIGNED
- category_code VARCHAR(50) NOT NULL
- category_name VARCHAR(150) NOT NULL
- is_active TINYINT(1) NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- category_id

Foreign Keys:
- parent_category_id -> product_categories.category_id

Indexes:
- UNIQUE(category_code)
- UNIQUE(category_name)

Constraints:
- self-referencing parent allowed for hierarchy

Relationships:
- One category to many child categories
- One category to many products

## 11) products
Purpose: Product/material master records.

Columns:
- product_id BIGINT UNSIGNED AI
- category_id BIGINT UNSIGNED NOT NULL
- product_code VARCHAR(60) NOT NULL
- product_name VARCHAR(200) NOT NULL
- unit_of_measure VARCHAR(30) NOT NULL
- reorder_level DECIMAL(18,3) NOT NULL
- is_active TINYINT(1) NOT NULL
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Primary Key:
- product_id

Foreign Keys:
- category_id -> product_categories.category_id

Indexes:
- UNIQUE(product_code)
- UNIQUE(product_name)
- INDEX(category_id)

Constraints:
- reorder_level >= 0

Relationships:
- Many products belong to one category
- One product to many price_history rows
- One product to many receipt_items
- One product to many inventory rows

## 12) price_history
Purpose: Time-variant supplier pricing per product.

Columns:
- price_history_id BIGINT UNSIGNED AI
- product_id BIGINT UNSIGNED NOT NULL
- supplier_id BIGINT UNSIGNED NOT NULL
- effective_from DATE NOT NULL
- effective_to DATE
- unit_price DECIMAL(18,4) NOT NULL
- currency_code CHAR(3) NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- price_history_id

Foreign Keys:
- product_id -> products.product_id
- supplier_id -> suppliers.supplier_id

Indexes:
- INDEX(product_id, supplier_id)
- INDEX(effective_from, effective_to)

Constraints:
- unit_price >= 0
- effective_to >= effective_from when set

Relationships:
- Many price history rows for each supplier-product pair over time

## 13) receipts
Purpose: Goods receipt header from supplier deliveries.

Columns:
- receipt_id BIGINT UNSIGNED AI
- supplier_id BIGINT UNSIGNED NOT NULL
- site_id BIGINT UNSIGNED NOT NULL
- project_id BIGINT UNSIGNED
- receipt_number VARCHAR(100) NOT NULL
- receipt_date DATE NOT NULL
- status VARCHAR(30) NOT NULL
- created_by_user_id BIGINT UNSIGNED NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- receipt_id

Foreign Keys:
- supplier_id -> suppliers.supplier_id
- site_id -> sites.site_id
- project_id -> projects.project_id
- created_by_user_id -> users.user_id

Indexes:
- UNIQUE(receipt_number)
- INDEX(supplier_id, receipt_date)
- INDEX(site_id)

Constraints:
- status in allowed set

Relationships:
- One receipt to many receipt_items
- Many receipts per supplier/site/project
- Optional one receipt to many invoices

## 14) receipt_items
Purpose: Line items received on a receipt.

Columns:
- receipt_item_id BIGINT UNSIGNED AI
- receipt_id BIGINT UNSIGNED NOT NULL
- product_id BIGINT UNSIGNED NOT NULL
- quantity DECIMAL(18,3) NOT NULL
- unit_cost DECIMAL(18,4) NOT NULL
- line_total DECIMAL(18,4) NOT NULL

Primary Key:
- receipt_item_id

Foreign Keys:
- receipt_id -> receipts.receipt_id
- product_id -> products.product_id

Indexes:
- UNIQUE(receipt_id, product_id)
- INDEX(product_id)

Constraints:
- quantity > 0
- costs >= 0

Relationships:
- Many receipt items belong to one receipt
- Many receipt items reference one product
- Receipt items can feed inventory_transactions

## 15) invoices
Purpose: Supplier billing documents.

Columns:
- invoice_id BIGINT UNSIGNED AI
- supplier_id BIGINT UNSIGNED NOT NULL
- contract_id BIGINT UNSIGNED
- receipt_id BIGINT UNSIGNED
- invoice_number VARCHAR(100) NOT NULL
- invoice_date DATE NOT NULL
- due_date DATE NOT NULL
- invoice_total DECIMAL(18,4) NOT NULL
- status VARCHAR(30) NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- invoice_id

Foreign Keys:
- supplier_id -> suppliers.supplier_id
- contract_id -> supplier_contracts.contract_id
- receipt_id -> receipts.receipt_id

Indexes:
- UNIQUE(invoice_number)
- INDEX(supplier_id, invoice_date)
- INDEX(status)

Constraints:
- due_date >= invoice_date
- invoice_total >= 0
- status in allowed set

Relationships:
- Many invoices belong to one supplier
- Optional relation to one contract and one receipt
- One invoice to many payments

## 16) payments
Purpose: Payments made toward invoices.

Columns:
- payment_id BIGINT UNSIGNED AI
- invoice_id BIGINT UNSIGNED NOT NULL
- payment_reference VARCHAR(100) NOT NULL
- payment_date DATE NOT NULL
- amount DECIMAL(18,4) NOT NULL
- payment_method VARCHAR(30) NOT NULL
- paid_by_user_id BIGINT UNSIGNED NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- payment_id

Foreign Keys:
- invoice_id -> invoices.invoice_id
- paid_by_user_id -> users.user_id

Indexes:
- UNIQUE(payment_reference)
- INDEX(invoice_id, payment_date)

Constraints:
- amount > 0
- method in allowed set

Relationships:
- Many payments apply to one invoice

## 17) expense_categories
Purpose: Classification list for expenses.

Columns:
- expense_category_id BIGINT UNSIGNED AI
- category_code VARCHAR(50) NOT NULL
- category_name VARCHAR(150) NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- expense_category_id

Foreign Keys:
- None

Indexes:
- UNIQUE(category_code)
- UNIQUE(category_name)

Constraints:
- unique code and name

Relationships:
- One expense category to many expenses

## 18) expenses
Purpose: Non-inventory operational/project expenses.

Columns:
- expense_id BIGINT UNSIGNED AI
- expense_category_id BIGINT UNSIGNED NOT NULL
- site_id BIGINT UNSIGNED NOT NULL
- project_id BIGINT UNSIGNED
- supplier_id BIGINT UNSIGNED
- expense_date DATE NOT NULL
- amount DECIMAL(18,4) NOT NULL
- description VARCHAR(500)
- created_by_user_id BIGINT UNSIGNED NOT NULL
- created_at DATETIME NOT NULL

Primary Key:
- expense_id

Foreign Keys:
- expense_category_id -> expense_categories.expense_category_id
- site_id -> sites.site_id
- project_id -> projects.project_id
- supplier_id -> suppliers.supplier_id
- created_by_user_id -> users.user_id

Indexes:
- INDEX(site_id, expense_date)
- INDEX(project_id)

Constraints:
- amount > 0

Relationships:
- Many expenses belong to one category and site
- Optional link to project and supplier

## 19) inventory
Purpose: Current stock balance per site and product.

Columns:
- inventory_id BIGINT UNSIGNED AI
- site_id BIGINT UNSIGNED NOT NULL
- product_id BIGINT UNSIGNED NOT NULL
- quantity_on_hand DECIMAL(18,3) NOT NULL
- quantity_reserved DECIMAL(18,3) NOT NULL
- last_transaction_at DATETIME

Primary Key:
- inventory_id

Foreign Keys:
- site_id -> sites.site_id
- product_id -> products.product_id

Indexes:
- UNIQUE(site_id, product_id)
- INDEX(product_id)

Constraints:
- quantities >= 0

Relationships:
- One inventory record has many inventory_transactions

## 20) inventory_transactions
Purpose: Immutable stock movement ledger.

Columns:
- transaction_id BIGINT UNSIGNED AI
- inventory_id BIGINT UNSIGNED NOT NULL
- receipt_item_id BIGINT UNSIGNED
- project_id BIGINT UNSIGNED
- transaction_type VARCHAR(30) NOT NULL
- quantity_delta DECIMAL(18,3) NOT NULL
- reference_number VARCHAR(100)
- remarks VARCHAR(500)
- transaction_at DATETIME NOT NULL
- created_by_user_id BIGINT UNSIGNED NOT NULL

Primary Key:
- transaction_id

Foreign Keys:
- inventory_id -> inventory.inventory_id
- receipt_item_id -> receipt_items.receipt_item_id
- project_id -> projects.project_id
- created_by_user_id -> users.user_id

Indexes:
- INDEX(inventory_id, transaction_at)
- INDEX(project_id)

Constraints:
- transaction_type in allowed set
- quantity_delta != 0

Relationships:
- Many transactions belong to one inventory record
- Optional transaction source from receipt item
- Optional consumption by project
- One adjustment transaction may have one stock_adjustments row

## 21) stock_adjustments
Purpose: Approval and reason metadata for adjustment transactions.

Columns:
- stock_adjustment_id BIGINT UNSIGNED AI
- transaction_id BIGINT UNSIGNED NOT NULL
- adjustment_reason VARCHAR(255) NOT NULL
- approved_by_user_id BIGINT UNSIGNED
- approved_at DATETIME

Primary Key:
- stock_adjustment_id

Foreign Keys:
- transaction_id -> inventory_transactions.transaction_id
- approved_by_user_id -> users.user_id

Indexes:
- UNIQUE(transaction_id)

Constraints:
- transaction has at most one stock adjustment record

Relationships:
- One-to-one extension of inventory_transactions for ADJUSTMENT type

## 22) audit_logs
Purpose: Immutable business/security audit trail.

Columns:
- audit_log_id BIGINT UNSIGNED AI
- actor_user_id BIGINT UNSIGNED
- action_code VARCHAR(100) NOT NULL
- entity_name VARCHAR(100) NOT NULL
- entity_id VARCHAR(100) NOT NULL
- old_values JSON
- new_values JSON
- request_id VARCHAR(100)
- ip_address VARCHAR(45)
- created_at DATETIME NOT NULL

Primary Key:
- audit_log_id

Foreign Keys:
- actor_user_id -> users.user_id

Indexes:
- INDEX(entity_name, entity_id)
- INDEX(created_at)

Constraints:
- none beyond FK and not-null fields

Relationships:
- Many audit logs can be generated by one user

## 23) login_history
Purpose: Track authentication attempts and sessions.

Columns:
- login_history_id BIGINT UNSIGNED AI
- user_id BIGINT UNSIGNED NOT NULL
- login_at DATETIME NOT NULL
- logout_at DATETIME
- ip_address VARCHAR(45)
- user_agent VARCHAR(255)
- login_status VARCHAR(30) NOT NULL
- failure_reason VARCHAR(255)

Primary Key:
- login_history_id

Foreign Keys:
- user_id -> users.user_id

Indexes:
- INDEX(user_id, login_at)

Constraints:
- login_status in allowed set

Relationships:
- Many login history rows per user

## 24) attachments
Purpose: File metadata attached to any entity (polymorphic reference).

Columns:
- attachment_id BIGINT UNSIGNED AI
- entity_name VARCHAR(100) NOT NULL
- entity_id BIGINT UNSIGNED NOT NULL
- file_name VARCHAR(255) NOT NULL
- file_path VARCHAR(500) NOT NULL
- mime_type VARCHAR(100)
- file_size_bytes BIGINT UNSIGNED NOT NULL
- checksum_sha256 CHAR(64)
- uploaded_by_user_id BIGINT UNSIGNED NOT NULL
- uploaded_at DATETIME NOT NULL

Primary Key:
- attachment_id

Foreign Keys:
- uploaded_by_user_id -> users.user_id

Indexes:
- INDEX(entity_name, entity_id)

Constraints:
- file_size_bytes > 0

Relationships:
- Many attachments uploaded by one user
- Logical polymorphic relationship to many business entities

## 25) notifications
Purpose: User-facing system notifications.

Columns:
- notification_id BIGINT UNSIGNED AI
- user_id BIGINT UNSIGNED NOT NULL
- notification_type VARCHAR(50) NOT NULL
- subject VARCHAR(200) NOT NULL
- message TEXT NOT NULL
- is_read TINYINT(1) NOT NULL
- created_at DATETIME NOT NULL
- read_at DATETIME

Primary Key:
- notification_id

Foreign Keys:
- user_id -> users.user_id

Indexes:
- INDEX(user_id, is_read)

Constraints:
- none beyond FK and not-null fields

Relationships:
- Many notifications belong to one user

## 26) settings
Purpose: Configurable application settings.

Columns:
- setting_id BIGINT UNSIGNED AI
- setting_key VARCHAR(150) NOT NULL
- setting_value TEXT NOT NULL
- data_type VARCHAR(30) NOT NULL
- is_sensitive TINYINT(1) NOT NULL
- updated_by_user_id BIGINT UNSIGNED
- updated_at DATETIME NOT NULL

Primary Key:
- setting_id

Foreign Keys:
- updated_by_user_id -> users.user_id

Indexes:
- UNIQUE(setting_key)

Constraints:
- data_type in allowed set

Relationships:
- Many setting updates can reference one user

---

## Relationship Explanations (Complete)
1. users <-> roles is many-to-many via user_roles because one user can hold multiple roles and one role can be assigned to many users.
2. roles <-> permissions is many-to-many via role_permissions because role definitions aggregate multiple permissions and permissions are reused across roles.
3. sites -> projects is one-to-many because each project runs at one primary site, while each site may host multiple projects.
4. suppliers -> supplier_contracts is one-to-many because suppliers can have multiple contracts over time.
5. product_categories self-reference forms category trees (parent-child) to support classification depth without denormalization.
6. product_categories -> products is one-to-many because each product belongs to exactly one category.
7. products + suppliers -> price_history is many-to-many over time, decomposed into a history table with effective dates for temporal pricing.
8. suppliers/sites/projects/users -> receipts associates delivery headers with source supplier, destination site, optional project, and creator user.
9. receipts -> receipt_items is one-to-many since each receipt has multiple product lines.
10. products -> receipt_items is one-to-many because products can appear on many receipt lines.
11. suppliers/contracts/receipts -> invoices allows billing linked to supplier always, and optionally to contract and receipt context.
12. invoices -> payments is one-to-many because invoices may be settled in partial or multiple payments.
13. expense_categories/sites/projects/suppliers/users -> expenses allows categorized spending tied to location, optional project/vendor, and creator.
14. sites + products -> inventory enforces one current balance row per site-product pair.
15. inventory -> inventory_transactions is one-to-many immutable ledger relation; balances are derived/maintained from these entries.
16. receipt_items -> inventory_transactions optional link captures inbound stock provenance from receiving.
17. projects -> inventory_transactions optional link attributes stock usage/movement to a project.
18. inventory_transactions -> stock_adjustments is one-to-one extension for adjustment-only metadata and approvals.
19. users -> audit_logs one-to-many records who performed business actions.
20. users -> login_history one-to-many tracks authentication attempts over time.
21. users -> attachments one-to-many records uploader ownership; entity_name/entity_id provide polymorphic target reference.
22. users -> notifications one-to-many supports inbox-style message delivery.
23. users -> settings (updated_by_user_id) tracks who changed configuration values.
