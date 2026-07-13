from django import forms

from src.infrastructure.persistence.models import Supplier, Warehouse


class ReportingFilterForm(forms.Form):
    REPORT_CHOICES = [
        ("expenses_daily", "Daily Expenses"),
        ("expenses_weekly", "Weekly Expenses"),
        ("expenses_monthly", "Monthly Expenses"),
        ("supplier_balance", "Supplier Balance"),
        ("products_bought", "Products Bought"),
        ("outstanding_supplier_balances", "Outstanding Supplier Balances"),
        ("site_expense_summary", "Site Expense Summary"),
        ("receipt_history_log", "Receipt History Log"),
    ]

    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("custom", "Custom Range"),
    ]

    report_type = forms.ChoiceField(choices=REPORT_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False, widget=forms.Select(attrs={"class": "form-select"}))
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

    def __init__(self, *args, **kwargs):
        supplier_queryset = kwargs.pop("supplier_queryset", None)
        site_queryset = kwargs.pop("site_queryset", None)
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = (site_queryset or Warehouse.objects).order_by("name")
        self.fields["supplier"].queryset = (supplier_queryset or Supplier.objects).order_by("name")
