from django.contrib import admin

from src.infrastructure.persistence.models import (
    AuditLog,
    Contract,
    Expense,
    ExpenseCategory,
    InventoryTransaction,
    Invoice,
    LoginHistory,
    NotificationQueue,
    PasswordHistory,
    Payment,
    PaymentAllocation,
    ProductPrice,
    Receipt,
    ReceiptEditLog,
    ReceiptLine,
    SiteStock,
    SupplierSite,
    UserSite,
    UserActivityLog,
    UserSecurityProfile,
)


@admin.register(UserSecurityProfile)
class UserSecurityProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "failed_login_attempts",
        "account_locked_until",
        "inactivity_days_limit",
        "force_password_change",
        "updated_at",
    )
    search_fields = ("user__username",)
    list_filter = ("force_password_change",)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("username", "was_successful", "ip_address", "login_time", "created_at")
    list_filter = ("was_successful", "login_time", "created_at")
    search_fields = ("username", "ip_address")


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username",)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "path", "created_at")
    list_filter = ("method", "created_at")
    search_fields = ("user__username", "path", "action")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("table_name", "record_id", "action_type", "actor", "date_time")
    search_fields = ("actor", "action", "table_name", "record_id", "reason")


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ("channel", "recipient", "status", "created_at")
    list_filter = ("status", "channel")
    search_fields = ("recipient",)


class ReceiptLineInline(admin.TabularInline):
    model = ReceiptLine
    extra = 0


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "supplier", "warehouse", "source_type", "receipt_date", "is_recorded", "created_at")
    list_filter = ("source_type", "is_recorded", "receipt_date")
    search_fields = ("receipt_number", "supplier__name")
    inlines = [ReceiptLineInline]


@admin.register(ReceiptLine)
class ReceiptLineAdmin(admin.ModelAdmin):
    list_display = ("receipt", "item", "product", "quantity", "unit_price", "line_total", "created_at")
    search_fields = ("receipt__receipt_number", "item__name", "item__sku")


@admin.register(ReceiptEditLog)
class ReceiptEditLogAdmin(admin.ModelAdmin):
    list_display = ("receipt", "field_name", "editor", "edit_date", "edited_at")
    list_filter = ("edit_date",)
    search_fields = ("receipt__receipt_number", "field_name", "reason", "editor__username")


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "site", "supplier", "date", "amount", "created_at")
    list_filter = ("category", "site", "date")
    search_fields = ("description", "supplier__name", "site__name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "supplier", "site", "date", "invoice_date", "amount", "status")
    list_filter = ("status", "site", "invoice_date")
    search_fields = ("invoice_number", "supplier__name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("supplier", "site", "receipt", "payment_date", "amount", "method", "reference_number")
    list_filter = ("site", "payment_date", "method")
    search_fields = ("supplier__name", "reference", "description")


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ("payment", "receipt", "amount_allocated", "created_at")
    search_fields = ("payment__id", "receipt__receipt_number")


@admin.register(UserSite)
class UserSiteAdmin(admin.ModelAdmin):
    list_display = ("user", "site", "created_at")
    search_fields = ("user__username", "site__name")


@admin.register(SupplierSite)
class SupplierSiteAdmin(admin.ModelAdmin):
    list_display = ("supplier", "site", "created_at")
    search_fields = ("supplier__name", "site__name")


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ("product", "effective_date", "price", "created_at")
    list_filter = ("effective_date",)
    search_fields = ("product__product_code", "product__product_name", "product__item__name")


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("supplier", "start_date", "end_date", "contract_value", "status")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("supplier__name", "description")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "site", "product", "transaction_type", "quantity", "unit_cost", "reference_number", "entered_by")
    list_filter = ("transaction_type", "date", "site")
    search_fields = ("reference_number", "remarks", "product__product_code", "product__product_name")


@admin.register(SiteStock)
class SiteStockAdmin(admin.ModelAdmin):
    list_display = ("site", "product", "quantity_on_hand")
    search_fields = ("site__name", "product__product_code", "product__product_name")
