# Construction ERP Deliverables (Django + DRF)

## Tech Stack Used
- Django 5
- Django REST Framework
- SQLite (offline) / MySQL (online)
- Django ORM migrations

## 1. Database Schema
Implemented in Django models and migrations:
- src/infrastructure/persistence/models/inventory_models.py
- src/infrastructure/persistence/models/cross_cutting_models.py
- src/infrastructure/persistence/models/auth_models.py
- src/infrastructure/persistence/migrations/0002_contract_productprice_auditlog_action_type_and_more.py

### Implemented Tables and Key Fields
- User (Django auth): username, password hash, email, full name (first_name + last_name), last_login, role via Group.
- Warehouse (Site): id, code, name, location, status.
- Supplier: id, name, phone, address, email.
- Product: id, product_code, product_name, unit_of_measure, item fk.
- ProductPrice: id, product fk, effective_date, price.
- UserSite: user fk, site fk (many-to-many user/site assignment).
- SupplierSite: supplier fk, site fk (many-to-many supplier/site mapping).
- Receipt: id, receipt_number (immutable + unique), supplier fk, warehouse/site fk, date, entered_by, edited_by, reason_for_edit, total_amount.
- ReceiptLine: receipt fk, product fk, item fk, quantity, unit_price (snapshot), total.
- Payment: supplier fk, receipt fk optional, invoice fk optional, amount, method enum, date, reference_number.
- PaymentAllocation: payment fk, receipt fk, amount_allocated (supports one payment to many receipts and partial payments).
- Contract: supplier fk, start_date, end_date, description, contract_value, status.
- ExpenseCategory: fixed lookup entries.
- Expense: site fk, category fk, amount, description, date, entered_by(created_by).
- Invoice: supplier fk, site fk, invoice_number, date, amount, status.
- AuditLog: user fk, table_name, record_id, action_type, reason, date_time, previous state metadata.
- LoginHistory: user fk, login_time, ip_address.

### Critical Indexes Added
- Receipt.receipt_number
- Receipt.receipt_date + supplier
- Payment.payment_date + supplier
- Expense.date + site
- AuditLog.table_name + record_id + date_time
- ProductPrice.product + effective_date
- Supplier.name
- Warehouse.status + name

### Audit Trigger Logic
Audit integrity is enforced in the receipt edit service and persisted to AuditLog with pre-edit snapshots:
- src/application/procurement/services/receipt_service.py

Equivalent SQL trigger logic (for direct DB deployments):
```sql
CREATE TRIGGER trg_receipt_before_update
BEFORE UPDATE ON persistence_receipt
FOR EACH ROW
BEGIN
  IF NEW.receipt_number <> OLD.receipt_number THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Receipt number is immutable';
  END IF;
END;
```

## 2. API Endpoints (REST)
Implemented routes:
- GET/POST /api/v1/sites/
- GET/POST /api/v1/suppliers/
- GET/POST /api/v1/products/
- GET/POST /api/v1/product-prices/
- GET/POST /api/v1/receipts/
- GET/PUT/PATCH /api/v1/receipts/:id/
- GET/POST /api/v1/payments/
- GET/POST /api/v1/contracts/
- GET /api/v1/expenses/categories/
- GET/POST /api/v1/expenses/
- GET/POST /api/v1/invoices/
- GET /api/v1/reports/?type=...

Web workflow endpoints added for finalized UX:
- GET/POST /payments/create/
- GET /payments/outstanding/?supplier_id=...

Files:
- src/presentation/api/v1/urls/__init__.py
- src/presentation/api/v1/views/erp_views.py
- src/presentation/api/v1/serializers/erp_serializers.py

### Authentication + RBAC Middleware
- DRF auth in config/settings.py
- Role middleware class: src/presentation/api/permissions/construction_rbac.py
- Seeded roles: Admin, ProjectManager, Accountant, SiteEngineer

## 3. Core Business Logic
### Create Receipt
- Validates header and lines.
- Requires non-empty lines.
- For each line, resolves Product and snapshots historical price from ProductPrice where effective_date <= receipt_date.
- Stores unit_price snapshot in ReceiptLine.
- Computes line totals and receipt total_amount.

### Allocate Payment Across Multiple Receipts
- Fetches unpaid/partially paid receipts by supplier.
- Allows manual amount allocation per selected receipt.
- Validates sum(allocations) <= payment amount.
- Persists payment and PaymentAllocation rows atomically.

### Edit Receipt
- Requires reason_for_edit.
- Captures full previous receipt + lines snapshot.
- Applies mutable updates only (receipt_number immutable).
- Writes per-field ReceiptEditLog and global AuditLog with previous_state payload.
- Updates edited_by and reason_for_edit.

### Supplier Outstanding Balance
- Supplier balance uses:
  outstanding = (sum(receipt totals) + sum(invoice amounts)) - sum(payment amounts)
- Site-filtered outstanding report is implemented.

File:
- src/application/reporting/services/report_service.py
- src/application/payments/services/payment_service.py

## 4. Project Folder Structure (Current Stack)
Recommended and now aligned structure:
- src/infrastructure/persistence/models
- src/infrastructure/persistence/migrations
- src/application/*/services
- src/presentation/api/v1/views
- src/presentation/api/v1/serializers
- src/presentation/api/permissions
- src/presentation/web/views
- src/presentation/web/forms
- docs/architecture

Finalized Receipt-first UI modules:
- templates/receipt/receipt_create.html
- templates/receipt/receipt_detail.html
- templates/payments/payment_create.html

## 5. Seed Data
Command:
```bash
python manage.py seed_construction_erp
```
Seeds:
- Roles and role permissions (Admin, ProjectManager, Accountant, SiteEngineer)
- Expense categories:
  - Buying Materials
  - Fuel
  - Labour
  - Transport
  - Accommodation
  - Repairs
  - Contractor Payment
  - Equipment

File:
- src/infrastructure/persistence/management/commands/seed_construction_erp.py
