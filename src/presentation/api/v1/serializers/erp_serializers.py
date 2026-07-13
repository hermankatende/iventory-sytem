from decimal import Decimal

from rest_framework import serializers

from src.infrastructure.persistence.models import (
    Contract,
    Expense,
    ExpenseCategory,
    Invoice,
    Payment,
    Product,
    ProductPrice,
    Receipt,
    Supplier,
    Warehouse,
)


class SiteSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="name", required=False)

    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "site_name", "location", "status"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "phone", "address", "email"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "product_code", "product_name", "unit_of_measure", "item", "category"]


class ProductPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPrice
        fields = ["id", "product", "effective_date", "price"]


class ReceiptLineInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, min_value=1)
    item_id = serializers.IntegerField(required=False, min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)


class ReceiptCreateSerializer(serializers.Serializer):
    receipt_number = serializers.CharField(max_length=64)
    supplier_id = serializers.IntegerField(min_value=1)
    site_id = serializers.IntegerField(min_value=1)
    source_type = serializers.ChoiceField(choices=Receipt.SOURCE_TYPES)
    date = serializers.DateField(source="receipt_date")
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = ReceiptLineInputSerializer(many=True)


class ReceiptEditSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(required=False, min_value=1)
    site_id = serializers.IntegerField(required=False, min_value=1)
    source_type = serializers.ChoiceField(required=False, choices=Receipt.SOURCE_TYPES)
    receipt_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    reason_for_edit = serializers.CharField(max_length=500)


class PaymentSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source="payment_date", required=False)

    class Meta:
        model = Payment
        fields = [
            "id",
            "supplier",
            "receipt",
            "invoice",
            "site",
            "amount",
            "method",
            "date",
            "reference",
            "reference_number",
        ]


class PaymentOutstandingQuerySerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(min_value=1)


class PaymentAllocationRowSerializer(serializers.Serializer):
    receipt_id = serializers.IntegerField(min_value=1)
    amount_allocated = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))


class PaymentCreateWithAllocationsSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(min_value=1)
    site_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    payment_date = serializers.DateField(required=False)
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)
    reference_number = serializers.CharField(required=False, allow_blank=True, max_length=64)
    allocations = PaymentAllocationRowSerializer(many=True)


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ["id", "supplier", "start_date", "end_date", "description", "contract_value", "status"]


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "site", "category", "amount", "description", "date", "created_by", "supplier"]
        read_only_fields = ["created_by"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "supplier", "site", "invoice_number", "date", "amount", "status"]


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "code", "name", "is_active"]


class ReceiptSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(source="warehouse_id", read_only=True)
    date = serializers.DateField(source="receipt_date", read_only=True)

    class Meta:
        model = Receipt
        fields = [
            "id",
            "receipt_number",
            "supplier_id",
            "site_id",
            "date",
            "source_type",
            "entered_by",
            "edited_by",
            "reason_for_edit",
            "total_amount",
            "is_recorded",
        ]
