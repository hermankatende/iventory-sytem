from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.application.expenses.services.expense_service import ExpenseService
from src.infrastructure.persistence.models import Supplier
from src.presentation.web.forms.expense_forms import ExpenseFilterForm, ExpenseForm
from src.shared.utils.site_context import site_scope_from_request, switchable_sites_for_user


expense_service = ExpenseService()


@login_required
@require_http_methods(["GET", "POST"])
def expense_management_view(request):
    expense_service.ensure_default_categories()

    scope = site_scope_from_request(request)
    sites_qs = switchable_sites_for_user(request.user)
    suppliers_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()

    create_form = ExpenseForm(
        request.POST or None,
        request.FILES or None,
        supplier_queryset=suppliers_qs,
        site_queryset=sites_qs,
    )
    if request.method == "POST" and create_form.is_valid():
        data = create_form.cleaned_data
        try:
            if scope["assigned_site_ids"] is not None and data["site"].id not in scope["assigned_site_ids"]:
                raise ValidationException("You are not assigned to the selected site.")
            expense_service.create_expense(
                category_id=data["category"].id,
                site_id=data["site"].id,
                supplier_id=data["supplier"].id if data.get("supplier") else None,
                date=data["date"],
                amount=float(data["amount"]),
                description=data.get("description", ""),
                attachment=data.get("attachment"),
                created_by=request.user,
            )
            messages.success(request, "Expense recorded successfully.")
            create_form = ExpenseForm(supplier_queryset=suppliers_qs, site_queryset=sites_qs)
        except ValidationException as exc:
            create_form.add_error(None, str(exc))

    filter_form = ExpenseFilterForm(request.GET or None, supplier_queryset=suppliers_qs, site_queryset=sites_qs)
    filter_form.is_valid()
    cleaned = getattr(filter_form, "cleaned_data", {})

    expenses = expense_service.list_expenses(
        start_date=cleaned.get("start_date") if cleaned else None,
        end_date=cleaned.get("end_date") if cleaned else None,
        site_id=cleaned.get("site").id if cleaned and cleaned.get("site") else None,
        supplier_id=cleaned.get("supplier").id if cleaned and cleaned.get("supplier") else None,
        category_id=cleaned.get("category").id if cleaned and cleaned.get("category") else None,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )[:500]

    monthly_rows = expense_service.monthly_totals(
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )
    yearly_rows = expense_service.yearly_totals(
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )

    return render(
        request,
        "expenses/expense_management.html",
        {
            "create_form": create_form,
            "filter_form": filter_form,
            "expenses": expenses,
            "monthly_rows": monthly_rows,
            "yearly_rows": yearly_rows,
        },
    )
