from django import forms

from src.infrastructure.persistence.models import InventoryTransaction, Product, ProductCategory, Warehouse


class ProductCategoryForm(forms.Form):
    name = forms.CharField(max_length=128, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )


class ProductRegistrationForm(forms.Form):
    sku = forms.CharField(max_length=64, widget=forms.TextInput(attrs={"class": "form-control"}))
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    reorder_level = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    unit_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    product_code = forms.CharField(max_length=64, widget=forms.TextInput(attrs={"class": "form-control"}))
    category_id = forms.ModelChoiceField(
        queryset=ProductCategory.objects.none(),
        required=False,
        empty_label="Uncategorized",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    barcode = forms.CharField(required=False, max_length=128, widget=forms.TextInput(attrs={"class": "form-control"}))
    unit_of_measure = forms.CharField(max_length=32, required=False, initial="unit", widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_id"].queryset = ProductCategory.objects.order_by("name")


class StockInOutForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    warehouse_id = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    qty = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    reason = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse_id"].queryset = Warehouse.objects.order_by("name")


class StockAdjustmentForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    warehouse_id = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    delta = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    reason = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse_id"].queryset = Warehouse.objects.order_by("name")


class TransferForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    source_warehouse_id = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    destination_warehouse_id = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    qty = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    reason = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warehouses = Warehouse.objects.order_by("name")
        self.fields["source_warehouse_id"].queryset = warehouses
        self.fields["destination_warehouse_id"].queryset = warehouses

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get("source_warehouse_id")
        destination = cleaned.get("destination_warehouse_id")
        if source and destination and source.id == destination.id:
            self.add_error("destination_warehouse_id", "Destination must be different from source.")
        return cleaned


class InventoryFilterForm(forms.Form):
    search = forms.CharField(required=False, max_length=128, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search by name, SKU, code, barcode"}))
    category_id = forms.ModelChoiceField(
        queryset=ProductCategory.objects.none(),
        required=False,
        empty_label="All categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    warehouse_id = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        required=False,
        empty_label="All sites",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_id"].queryset = ProductCategory.objects.order_by("name")
        self.fields["warehouse_id"].queryset = Warehouse.objects.order_by("name")


class InventoryTransactionForm(forms.Form):
    site = forms.ModelChoiceField(queryset=Warehouse.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))
    product = forms.ModelChoiceField(queryset=Product.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))
    transaction_type = forms.ChoiceField(
        choices=InventoryTransaction.TRANSACTION_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        help_text="Enter the movement quantity. Issues and transfer-outs are stored as negative values.",
    )
    unit_cost = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    reference_number = forms.CharField(required=False, max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))

    def __init__(self, *args, **kwargs):
        site_queryset = kwargs.pop("site_queryset", None)
        product_queryset = kwargs.pop("product_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = (site_queryset or Warehouse.objects).order_by("name")
        self.fields["product"].queryset = (product_queryset or Product.objects).order_by("product_name", "product_code")


class BatchOperationForm(forms.Form):
    operation_type = forms.ChoiceField(
        choices=[
            ("STOCK_IN", "Stock In"),
            ("STOCK_OUT", "Stock Out"),
            ("TRANSFER", "Transfer"),
            ("ADJUST", "Adjustment"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    operations_json = forms.CharField(
        help_text="JSON array. Examples: [{\"item_id\":1,\"warehouse_id\":1,\"qty\":5}]",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
    )
