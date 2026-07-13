from django import forms

from src.infrastructure.persistence.models import Payment, Receipt, Supplier


class PaymentCreateForm(forms.Form):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    amount = forms.DecimalField(min_value=0.01, decimal_places=2, max_digits=14, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    payment_date = forms.DateField(widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    method = forms.ChoiceField(choices=Payment.METHOD_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    reference_number = forms.CharField(required=False, max_length=64, widget=forms.TextInput(attrs={"class": "form-control"}))
    allocations_json = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")


class SupplierReceiptFilterForm(forms.Form):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")


class ReceiptOutstandingForm(forms.Form):
    receipt = forms.ModelChoiceField(queryset=Receipt.objects.none())
    amount_allocated = forms.DecimalField(min_value=0.01, decimal_places=2, max_digits=14)
