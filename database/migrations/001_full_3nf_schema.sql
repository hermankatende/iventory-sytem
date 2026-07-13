-- Construction Inventory & Supplier Management System
-- MySQL 8+ 3NF schema

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS roles (
    role_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_name VARCHAR(100) NOT NULL,
    role_description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id),
    CONSTRAINT uq_roles_name UNIQUE (role_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS permissions (
    permission_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    permission_code VARCHAR(150) NOT NULL,
    permission_description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (permission_id),
    CONSTRAINT uq_permissions_code UNIQUE (permission_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_roles (
    user_role_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by_user_id BIGINT UNSIGNED NULL,
    PRIMARY KEY (user_role_id),
    CONSTRAINT uq_user_roles_user_role UNIQUE (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(role_id),
    CONSTRAINT fk_user_roles_assigned_by FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS role_permissions (
    role_permission_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_id BIGINT UNSIGNED NOT NULL,
    permission_id BIGINT UNSIGNED NOT NULL,
    granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_permission_id),
    CONSTRAINT uq_role_permissions_role_perm UNIQUE (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles(role_id),
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sites (
    site_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site_code VARCHAR(50) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    address_line1 VARCHAR(255) NULL,
    address_line2 VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    state_region VARCHAR(100) NULL,
    country VARCHAR(100) NULL,
    postal_code VARCHAR(30) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (site_id),
    CONSTRAINT uq_sites_code UNIQUE (site_code),
    CONSTRAINT uq_sites_name UNIQUE (site_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS projects (
    project_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site_id BIGINT UNSIGNED NOT NULL,
    project_code VARCHAR(50) NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status VARCHAR(30) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id),
    CONSTRAINT uq_projects_code UNIQUE (project_code),
    CONSTRAINT fk_projects_site FOREIGN KEY (site_id) REFERENCES sites(site_id),
    CONSTRAINT chk_projects_status CHECK (status IN ('PLANNED', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT chk_projects_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_code VARCHAR(50) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    tax_number VARCHAR(100) NULL,
    email VARCHAR(255) NULL,
    phone VARCHAR(50) NULL,
    address_line1 VARCHAR(255) NULL,
    address_line2 VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    state_region VARCHAR(100) NULL,
    country VARCHAR(100) NULL,
    postal_code VARCHAR(30) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (supplier_id),
    CONSTRAINT uq_suppliers_code UNIQUE (supplier_code),
    CONSTRAINT uq_suppliers_name UNIQUE (supplier_name),
    CONSTRAINT chk_suppliers_status CHECK (status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS supplier_contracts (
    contract_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_id BIGINT UNSIGNED NOT NULL,
    contract_number VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    payment_terms_days INT UNSIGNED NOT NULL DEFAULT 30,
    status VARCHAR(30) NOT NULL,
    notes VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contract_id),
    CONSTRAINT uq_supplier_contracts_number UNIQUE (contract_number),
    CONSTRAINT fk_supplier_contracts_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT chk_supplier_contracts_status CHECK (status IN ('DRAFT', 'ACTIVE', 'EXPIRED', 'TERMINATED')),
    CONSTRAINT chk_supplier_contracts_dates CHECK (end_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS product_categories (
    category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    parent_category_id BIGINT UNSIGNED NULL,
    category_code VARCHAR(50) NOT NULL,
    category_name VARCHAR(150) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (category_id),
    CONSTRAINT uq_product_categories_code UNIQUE (category_code),
    CONSTRAINT uq_product_categories_name UNIQUE (category_name),
    CONSTRAINT fk_product_categories_parent FOREIGN KEY (parent_category_id) REFERENCES product_categories(category_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_id BIGINT UNSIGNED NOT NULL,
    product_code VARCHAR(60) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    unit_of_measure VARCHAR(30) NOT NULL,
    reorder_level DECIMAL(18,3) NOT NULL DEFAULT 0.000,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    CONSTRAINT uq_products_code UNIQUE (product_code),
    CONSTRAINT uq_products_name UNIQUE (product_name),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
    CONSTRAINT chk_products_reorder_level CHECK (reorder_level >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS price_history (
    price_history_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id BIGINT UNSIGNED NOT NULL,
    supplier_id BIGINT UNSIGNED NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    unit_price DECIMAL(18,4) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'USD',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (price_history_id),
    CONSTRAINT fk_price_history_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_price_history_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT chk_price_history_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_price_history_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS receipts (
    receipt_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_id BIGINT UNSIGNED NOT NULL,
    site_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NULL,
    receipt_number VARCHAR(100) NOT NULL,
    receipt_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (receipt_id),
    CONSTRAINT uq_receipts_number UNIQUE (receipt_number),
    CONSTRAINT fk_receipts_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_receipts_site FOREIGN KEY (site_id) REFERENCES sites(site_id),
    CONSTRAINT fk_receipts_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_receipts_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_receipts_status CHECK (status IN ('DRAFT', 'POSTED', 'CANCELLED'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS receipt_items (
    receipt_item_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    receipt_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(18,3) NOT NULL,
    unit_cost DECIMAL(18,4) NOT NULL,
    line_total DECIMAL(18,4) NOT NULL,
    PRIMARY KEY (receipt_item_id),
    CONSTRAINT uq_receipt_items_receipt_product UNIQUE (receipt_id, product_id),
    CONSTRAINT fk_receipt_items_receipt FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id),
    CONSTRAINT fk_receipt_items_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT chk_receipt_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_receipt_items_unit_cost CHECK (unit_cost >= 0),
    CONSTRAINT chk_receipt_items_line_total CHECK (line_total >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    supplier_id BIGINT UNSIGNED NOT NULL,
    contract_id BIGINT UNSIGNED NULL,
    receipt_id BIGINT UNSIGNED NULL,
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    invoice_total DECIMAL(18,4) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (invoice_id),
    CONSTRAINT uq_invoices_number UNIQUE (invoice_number),
    CONSTRAINT fk_invoices_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_invoices_contract FOREIGN KEY (contract_id) REFERENCES supplier_contracts(contract_id),
    CONSTRAINT fk_invoices_receipt FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id),
    CONSTRAINT chk_invoices_dates CHECK (due_date >= invoice_date),
    CONSTRAINT chk_invoices_total CHECK (invoice_total >= 0),
    CONSTRAINT chk_invoices_status CHECK (status IN ('DRAFT', 'OPEN', 'PARTIALLY_PAID', 'PAID', 'VOID'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    invoice_id BIGINT UNSIGNED NOT NULL,
    payment_reference VARCHAR(100) NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(18,4) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    paid_by_user_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_id),
    CONSTRAINT uq_payments_reference UNIQUE (payment_reference),
    CONSTRAINT fk_payments_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    CONSTRAINT fk_payments_user FOREIGN KEY (paid_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_payments_amount CHECK (amount > 0),
    CONSTRAINT chk_payments_method CHECK (payment_method IN ('CASH', 'BANK_TRANSFER', 'CHEQUE', 'CARD'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory_transactions (
    inventory_transaction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    transaction_date DATE NOT NULL,
    reference_number VARCHAR(50) NULL,
    entered_by_user_id BIGINT UNSIGNED NULL,
    remarks TEXT NULL,
    PRIMARY KEY (inventory_transaction_id),
    CONSTRAINT fk_inventory_transactions_site FOREIGN KEY (site_id) REFERENCES sites(site_id),
    CONSTRAINT fk_inventory_transactions_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_inventory_transactions_entered_by FOREIGN KEY (entered_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_inventory_transactions_type CHECK (transaction_type IN ('PURCHASE_RECEIPT', 'SITE_ISSUE', 'ADJUSTMENT', 'TRANSFER_OUT', 'TRANSFER_IN'))
) ENGINE=InnoDB;

CREATE VIEW IF NOT EXISTS vw_SiteStock AS
SELECT
    ROW_NUMBER() OVER (ORDER BY site_id, product_id) AS id,
    site_id AS SiteID,
    product_id AS ProductID,
    SUM(quantity) AS QuantityOnHand
FROM inventory_transactions
GROUP BY site_id, product_id;

CREATE TABLE IF NOT EXISTS expense_categories (
    expense_category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_code VARCHAR(50) NOT NULL,
    category_name VARCHAR(150) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (expense_category_id),
    CONSTRAINT uq_expense_categories_code UNIQUE (category_code),
    CONSTRAINT uq_expense_categories_name UNIQUE (category_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expenses (
    expense_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    expense_category_id BIGINT UNSIGNED NOT NULL,
    site_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NULL,
    supplier_id BIGINT UNSIGNED NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(18,4) NOT NULL,
    description VARCHAR(500) NULL,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (expense_id),
    CONSTRAINT fk_expenses_category FOREIGN KEY (expense_category_id) REFERENCES expense_categories(expense_category_id),
    CONSTRAINT fk_expenses_site FOREIGN KEY (site_id) REFERENCES sites(site_id),
    CONSTRAINT fk_expenses_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_expenses_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_expenses_user FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_expenses_amount CHECK (amount > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity_on_hand DECIMAL(18,3) NOT NULL DEFAULT 0.000,
    quantity_reserved DECIMAL(18,3) NOT NULL DEFAULT 0.000,
    last_transaction_at DATETIME NULL,
    PRIMARY KEY (inventory_id),
    CONSTRAINT uq_inventory_site_product UNIQUE (site_id, product_id),
    CONSTRAINT fk_inventory_site FOREIGN KEY (site_id) REFERENCES sites(site_id),
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT chk_inventory_quantities CHECK (quantity_on_hand >= 0 AND quantity_reserved >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    inventory_id BIGINT UNSIGNED NOT NULL,
    receipt_item_id BIGINT UNSIGNED NULL,
    project_id BIGINT UNSIGNED NULL,
    transaction_type VARCHAR(30) NOT NULL,
    quantity_delta DECIMAL(18,3) NOT NULL,
    reference_number VARCHAR(100) NULL,
    remarks VARCHAR(500) NULL,
    transaction_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (transaction_id),
    CONSTRAINT fk_inventory_transactions_inventory FOREIGN KEY (inventory_id) REFERENCES inventory(inventory_id),
    CONSTRAINT fk_inventory_transactions_receipt_item FOREIGN KEY (receipt_item_id) REFERENCES receipt_items(receipt_item_id),
    CONSTRAINT fk_inventory_transactions_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_inventory_transactions_user FOREIGN KEY (created_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_inventory_transactions_type CHECK (transaction_type IN ('RECEIPT', 'ISSUE', 'TRANSFER_IN', 'TRANSFER_OUT', 'ADJUSTMENT')),
    CONSTRAINT chk_inventory_transactions_delta CHECK (quantity_delta <> 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stock_adjustments (
    stock_adjustment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_id BIGINT UNSIGNED NOT NULL,
    adjustment_reason VARCHAR(255) NOT NULL,
    approved_by_user_id BIGINT UNSIGNED NULL,
    approved_at DATETIME NULL,
    PRIMARY KEY (stock_adjustment_id),
    CONSTRAINT uq_stock_adjustments_transaction UNIQUE (transaction_id),
    CONSTRAINT fk_stock_adjustments_transaction FOREIGN KEY (transaction_id) REFERENCES inventory_transactions(transaction_id),
    CONSTRAINT fk_stock_adjustments_approved_by FOREIGN KEY (approved_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_user_id BIGINT UNSIGNED NULL,
    action_code VARCHAR(100) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    request_id VARCHAR(100) NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (audit_log_id),
    CONSTRAINT fk_audit_logs_actor FOREIGN KEY (actor_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS login_history (
    login_history_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    login_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_at DATETIME NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    login_status VARCHAR(30) NOT NULL,
    failure_reason VARCHAR(255) NULL,
    PRIMARY KEY (login_history_id),
    CONSTRAINT fk_login_history_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT chk_login_history_status CHECK (login_status IN ('SUCCESS', 'FAILED', 'LOCKED'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attachments (
    attachment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    entity_name VARCHAR(100) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NULL,
    file_size_bytes BIGINT UNSIGNED NOT NULL,
    checksum_sha256 CHAR(64) NULL,
    uploaded_by_user_id BIGINT UNSIGNED NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (attachment_id),
    CONSTRAINT fk_attachments_uploaded_by FOREIGN KEY (uploaded_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_attachments_size CHECK (file_size_bytes > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
    notification_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME NULL,
    PRIMARY KEY (notification_id),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS settings (
    setting_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    setting_key VARCHAR(150) NOT NULL,
    setting_value TEXT NOT NULL,
    data_type VARCHAR(30) NOT NULL,
    is_sensitive TINYINT(1) NOT NULL DEFAULT 0,
    updated_by_user_id BIGINT UNSIGNED NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (setting_id),
    CONSTRAINT uq_settings_key UNIQUE (setting_key),
    CONSTRAINT fk_settings_user FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id),
    CONSTRAINT chk_settings_data_type CHECK (data_type IN ('STRING', 'INT', 'DECIMAL', 'BOOLEAN', 'JSON'))
) ENGINE=InnoDB;

CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
CREATE INDEX idx_projects_site_id ON projects(site_id);
CREATE INDEX idx_supplier_contracts_supplier_id ON supplier_contracts(supplier_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_price_history_product_supplier ON price_history(product_id, supplier_id);
CREATE INDEX idx_price_history_dates ON price_history(effective_from, effective_to);
CREATE INDEX idx_receipts_supplier_date ON receipts(supplier_id, receipt_date);
CREATE INDEX idx_receipts_site_id ON receipts(site_id);
CREATE INDEX idx_receipt_items_product_id ON receipt_items(product_id);
CREATE INDEX idx_invoices_supplier_date ON invoices(supplier_id, invoice_date);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_payments_invoice_date ON payments(invoice_id, payment_date);
CREATE INDEX idx_expenses_site_date ON expenses(site_id, expense_date);
CREATE INDEX idx_expenses_project_id ON expenses(project_id);
CREATE INDEX idx_inventory_product_id ON inventory(product_id);
CREATE INDEX idx_inventory_transactions_inventory_date ON inventory_transactions(inventory_id, transaction_at);
CREATE INDEX idx_inventory_transactions_project_id ON inventory_transactions(project_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_name, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_login_history_user_date ON login_history(user_id, login_at);
CREATE INDEX idx_attachments_entity ON attachments(entity_name, entity_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);

SET FOREIGN_KEY_CHECKS = 1;
