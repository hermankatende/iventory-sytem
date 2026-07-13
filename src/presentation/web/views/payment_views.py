import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.application.payments.services.payment_service import PaymentService
from src.infrastructure.persistence.models import Supplier
from src.presentation.web.forms.payment_forms import PaymentCreateForm
from src.presentation.web.permissions import require_permission
from src.shared.utils.site_context import site_scope_from_request


payment_service = PaymentService()


@login_required
@require_permission("persistence.add_payment")
@require_http_methods(["GET", "POST"])
def payment_create_view(request):
    scope = site_scope_from_request(request)
    suppliers_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()

    form = PaymentCreateForm(request.POST or None, supplier_queryset=suppliers_qs)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            allocations = payment_service.parse_allocations_json(data["allocations_json"])
            payment = payment_service.create_payment_with_allocations(
                supplier_id=data["supplier"].id,
                amount=data["amount"],
                payment_date=data["payment_date"],
                method=data["method"],
                description=data.get("description", ""),
                reference_number=data.get("reference_number", ""),
                allocations=allocations,
                site_id=scope["active_site_id"],
                assigned_site_ids=scope["assigned_site_ids"],
                active_site_id=scope["active_site_id"],
            )
            messages.success(request, f"Payment {payment.id} saved with {len(allocations)} allocation(s).")
            return redirect("payment_create")
        except ValidationException as exc:
            form.add_error(None, str(exc))

    selected_supplier_id = request.GET.get("supplier_id") or request.POST.get("supplier")
    outstanding_rows = []
    if selected_supplier_id:
        try:
            outstanding_rows = payment_service.outstanding_receipts_for_supplier(
                supplier_id=int(selected_supplier_id),
                assigned_site_ids=scope["assigned_site_ids"],
                active_site_id=scope["active_site_id"],
            )
        except ValueError:
            outstanding_rows = []

    return render(
        request,
        "payments/payment_create.html",
        {
            "form": form,
            "outstanding_rows_json": json.dumps(outstanding_rows),
        },
    )


@login_required
@require_permission("persistence.view_payment")
@require_http_methods(["GET"])
def supplier_outstanding_api(request):
    scope = site_scope_from_request(request)
    supplier_id = request.GET.get("supplier_id")
    if not supplier_id:
        return JsonResponse({"rows": []})

    try:
        rows = payment_service.outstanding_receipts_for_supplier(
            supplier_id=int(supplier_id),
            assigned_site_ids=scope["assigned_site_ids"],
            active_site_id=scope["active_site_id"],
        )
    except ValueError:
        rows = []
    return JsonResponse({"rows": rows})
