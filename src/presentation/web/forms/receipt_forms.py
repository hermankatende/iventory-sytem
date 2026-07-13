from django import forms

from src.infrastructure.persistence.models import Item, Receipt, Supplier, Warehouse


class ReceiptCreateForm(forms.Form):
    receipt_number = forms.CharField(max_length=64, widget=forms.TextInput(attrs={"class": "form-control"}))
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    source_type = forms.ChoiceField(
        choices=Receipt.SOURCE_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    receipt_date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    scan_file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    lines_json = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        help_text="JSON list: [{\"item_id\": 1, \"quantity\": 5, \"unit_price\": 12.50}]",
    )

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        warehouse_queryset = kwargs.pop("warehouse_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")
        self.fields["warehouse"].queryset = (warehouse_queryset or Warehouse.objects).order_by("name")


class ReceiptHeaderEditForm(forms.Form):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    source_type = forms.ChoiceField(
        choices=Receipt.SOURCE_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    receipt_date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    scan_file = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    reason = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        warehouse_queryset = kwargs.pop("warehouse_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")
        self.fields["warehouse"].queryset = (warehouse_queryset or Warehouse.objects).order_by("name")


class ReceiptLineEditForm(forms.Form):
    line_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    reason = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = Item.objects.filter(is_active=True).order_by("name")


class ReceiptRecordForm(forms.Form):
    reason = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
