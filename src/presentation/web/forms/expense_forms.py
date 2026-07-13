from django import forms

from src.infrastructure.persistence.models import ExpenseCategory, Supplier, Warehouse


class ExpenseForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    site = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        required=False,
        empty_label="No supplier",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    amount = forms.DecimalField(min_value=0.01, decimal_places=2, max_digits=14, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        site_queryset = kwargs.pop("site_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ExpenseCategory.objects.filter(is_active=True).order_by("name")
        self.fields["site"].queryset = (site_queryset or Warehouse.objects).order_by("name")
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")


class ExpenseFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    site = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        required=False,
        empty_label="All sites",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        required=False,
        empty_label="All suppliers",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.none(),
        required=False,
        empty_label="All categories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        site_queryset = kwargs.pop("site_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = (site_queryset or Warehouse.objects).order_by("name")
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")
        self.fields["category"].queryset = ExpenseCategory.objects.filter(is_active=True).order_by("name")
