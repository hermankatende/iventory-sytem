from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]


class Item(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    reorder_level = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    barcode = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Warehouse(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("UNDER_CONSTRUCTION", "Under Construction"),
        ("COMPLETED", "Completed"),
    )

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="ACTIVE")

    class Meta:
        indexes = [models.Index(fields=["status", "name"])]


class StockLevel(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    qty_on_hand = models.IntegerField(default=0)
    qty_reserved = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("item", "warehouse")
        indexes = [models.Index(fields=["warehouse", "item"]) ]


class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ("IN", "IN"),
        ("OUT", "OUT"),
        ("ADJUST", "ADJUST"),
        ("TRANSFER", "TRANSFER"),
    )

    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=16, choices=MOVEMENT_TYPES)
    delta = models.IntegerField()
    reason = models.CharField(max_length=255)
    reference = models.CharField(max_length=64, blank=True)
    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="source_movements",
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="destination_movements",
    )
    batch_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]


class Product(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="product")
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL)
    product_code = models.CharField(max_length=64, unique=True)
    product_name = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=128, blank=True)
    is_barcode_ready = models.BooleanField(default=False)
    unit_of_measure = models.CharField(max_length=32, default="unit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["product_code"]), models.Index(fields=["barcode"])]


class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")
    effective_date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "effective_date")
        indexes = [models.Index(fields=["product", "effective_date"])]


class InventoryTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ("PURCHASE_RECEIPT", "Purchase Receipt"),
        ("SITE_ISSUE", "Site Issue"),
        ("ADJUSTMENT", "Adjustment"),
        ("TRANSFER_OUT", "Transfer Out"),
        ("TRANSFER_IN", "Transfer In"),
    )

    site = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="inventory_transactions")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="inventory_transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date = models.DateField(default=timezone.localdate)
    reference_number = models.CharField(max_length=50, blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["site", "product", "date"]),
            models.Index(fields=["transaction_type", "date"]),
            models.Index(fields=["reference_number"]),
        ]


class UserSite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_sites")
    site = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="site_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "site")
        indexes = [models.Index(fields=["user", "site"])]


class SupplierSite(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_sites")
    site = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="site_suppliers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("supplier", "site")
        indexes = [models.Index(fields=["supplier", "site"])]


class BatchOperation(models.Model):
    OPERATION_TYPES = (
        ("STOCK_IN", "STOCK_IN"),
        ("STOCK_OUT", "STOCK_OUT"),
        ("TRANSFER", "TRANSFER"),
        ("ADJUST", "ADJUST"),
    )

    batch_id = models.CharField(max_length=64, unique=True)
    operation_type = models.CharField(max_length=16, choices=OPERATION_TYPES)
    total_lines = models.PositiveIntegerField(default=0)
    processed_lines = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)


class Receipt(models.Model):
    SOURCE_TYPES = (
        ("SUPPLIER", "SUPPLIER"),
        ("COMPANY", "COMPANY"),
    )

    receipt_number = models.CharField(max_length=64, unique=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="receipts")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="receipts")
    source_type = models.CharField(max_length=16, choices=SOURCE_TYPES, default="COMPANY")
    receipt_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    reason_for_edit = models.TextField(blank=True)
    scan_file = models.FileField(upload_to="receipts/scans/", null=True, blank=True)
    is_recorded = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_receipts",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recorded_receipts",
    )
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entered_receipts",
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="edited_receipts",
    )
    recorded_at = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["receipt_number"]), models.Index(fields=["receipt_date", "supplier"])]

    def save(self, *args, **kwargs):
        if self.pk:
            original = Receipt.objects.filter(pk=self.pk).values("receipt_number").first()
            if original and original["receipt_number"] != self.receipt_number:
                raise ValidationError("Receipt number is permanent and cannot be changed.")
        super().save(*args, **kwargs)


class ReceiptLine(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT, related_name="receipt_lines")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("receipt", "item")
        indexes = [models.Index(fields=["receipt", "item"])]

    def save(self, *args, **kwargs):
        self.line_total = Decimal(self.quantity) * self.unit_price
        self.total = self.line_total
        super().save(*args, **kwargs)


class ReceiptEditLog(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="edit_logs")
    line = models.ForeignKey(ReceiptLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="edit_logs")
    field_name = models.CharField(max_length=128)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.CharField(max_length=255)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    edit_date = models.DateField(default=timezone.now)
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["receipt", "edit_date"]), models.Index(fields=["editor", "edited_at"])]


class ExpenseCategory(models.Model):
    CATEGORY_CHOICES = (
        ("BUYING_MATERIALS", "Buying Materials"),
        ("FUEL", "Fuel"),
        ("LABOUR", "Labour"),
        ("TRANSPORT", "Transport"),
        ("ACCOMMODATION", "Accommodation"),
        ("REPAIRS", "Repairs"),
        ("CONTRACTOR_PAYMENT", "Contractor Payment"),
        ("EQUIPMENT", "Equipment"),
        # Backward-compatible legacy code.
        ("CONTRACTOR_PAYMENTS", "Contractor Payments"),
        ("OTHER", "Other"),
    )

    code = models.CharField(max_length=64, unique=True, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=128, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = dict(self.CATEGORY_CHOICES).get(self.code, self.code.replace("_", " ").title())
        super().save(*args, **kwargs)


class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    site = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="expenses")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="expenses")
    date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="expenses/attachments/", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["date", "site"]),
            models.Index(fields=["category", "date"]),
            models.Index(fields=["supplier", "date"]),
        ]


class Invoice(models.Model):
    STATUS_CHOICES = (
        ("PAID", "Paid"),
        ("UNPAID", "Unpaid"),
        ("OVERDUE", "Overdue"),
    )

    invoice_number = models.CharField(max_length=64, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="invoices")
    site = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="invoices")
    date = models.DateField(default=timezone.localdate)
    invoice_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="UNPAID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["invoice_date", "supplier"]), models.Index(fields=["site", "status"])]


class Payment(models.Model):
    METHOD_CHOICES = (
        ("CASH", "Cash"),
        ("MOBILE_MONEY", "MM"),
        ("BANK", "Bank"),
        ("CHEQUE", "Cheque"),
    )

    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    receipt = models.ForeignKey(Receipt, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="payments")
    site = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=32, choices=METHOD_CHOICES, default="BANK")
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=64, blank=True)
    reference_number = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["payment_date", "supplier"]), models.Index(fields=["site", "payment_date"])]


class SiteStock(models.Model):
    site = models.ForeignKey(Warehouse, db_column="SiteID", on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, db_column="ProductID", on_delete=models.DO_NOTHING)
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, db_column="QuantityOnHand")

    class Meta:
        managed = False
        db_table = "vw_SiteStock"
        ordering = ["site_id", "product_id"]


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="payment_allocations")
    amount_allocated = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("payment", "receipt")
        indexes = [models.Index(fields=["payment", "receipt"])]


class Contract(models.Model):
    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("TERMINATED", "Terminated"),
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="contracts")
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)
    contract_value = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["supplier", "status"]), models.Index(fields=["start_date", "end_date"])]
