import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from src.application.common.exceptions.domain_exceptions import NotFoundException, ValidationException
from src.application.procurement.services.receipt_service import ReceiptService
from src.infrastructure.persistence.models import Product, ProductPrice, Supplier, Warehouse
from src.presentation.web.permissions import require_permission
from src.presentation.web.forms.receipt_forms import (
    ReceiptCreateForm,
    ReceiptHeaderEditForm,
    ReceiptLineEditForm,
    ReceiptRecordForm,
)
from src.shared.utils.app_logger import get_app_logger
from src.shared.utils.site_context import site_scope_from_request, switchable_sites_for_user


receipt_service = ReceiptService()
logger = get_app_logger("web.receipts")


@login_required
@require_permission("persistence.view_receipt")
@require_http_methods(["GET"])
def receipt_list_view(request):
    scope = site_scope_from_request(request)
    search = (request.GET.get("search") or "").strip()
    receipts = receipt_service.list_receipts(
        search=search,
        assigned_site_ids=scope["assigned_site_ids"],
        active_site_id=scope["active_site_id"],
    )
    return render(request, "receipt/receipt_list.html", {"receipts": receipts, "search": search})


@login_required
@require_permission("persistence.add_receipt")
@require_http_methods(["GET", "POST"])
def receipt_create_view(request):
    scope = site_scope_from_request(request)
    sites_qs = switchable_sites_for_user(request.user)
    suppliers_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()

    form = ReceiptCreateForm(
        request.POST or None,
        request.FILES or None,
        supplier_queryset=suppliers_qs,
        warehouse_queryset=sites_qs,
    )
    if request.method == "POST" and form.is_valid():
        try:
            lines = receipt_service.parse_lines_json(form.cleaned_data["lines_json"])
            selected_site = form.cleaned_data["warehouse"].id
            if scope["assigned_site_ids"] is not None and selected_site not in scope["assigned_site_ids"]:
                raise ValidationException("You are not assigned to the selected site.")

            receipt = receipt_service.create_receipt(
                receipt_number=form.cleaned_data["receipt_number"],
                supplier_id=form.cleaned_data["supplier"].id,
                warehouse_id=selected_site,
                source_type=form.cleaned_data["source_type"],
                receipt_date=form.cleaned_data["receipt_date"],
                notes=form.cleaned_data.get("notes", ""),
                scan_file=form.cleaned_data.get("scan_file"),
                lines=lines,
                created_by=request.user,
            )
            messages.success(request, f"Receipt created: {receipt.receipt_number}")
            logger.info("receipt.created_view by=%s receipt=%s", request.user.username, receipt.receipt_number)
            return redirect("receipt_detail", receipt_id=receipt.id)
        except ValidationException as exc:
            form.add_error(None, str(exc))

    products_payload = []
    for product in Product.objects.select_related("item").order_by("item__name"):
        latest_price = (
            ProductPrice.objects.filter(product_id=product.id)
            .order_by("-effective_date")
            .values_list("price", flat=True)
            .first()
        )
        products_payload.append(
            {
                "id": product.id,
                "item_id": product.item_id,
                "label": f"{product.product_code} - {product.product_name or product.item.name}",
                "name": product.product_name or product.item.name,
                "unit": product.unit_of_measure,
                "latest_price": float(latest_price) if latest_price is not None else 0.0,
            }
        )

    return render(
        request,
        "receipt/receipt_create.html",
        {
            "form": form,
            "entered_by": request.user,
            "products_json": json.dumps(products_payload),
        },
    )


@login_required
@require_permission("persistence.view_receipt")
@require_http_methods(["GET", "POST"])
def receipt_detail_view(request, receipt_id: int):
    scope = site_scope_from_request(request)
    try:
        receipt = receipt_service.get_receipt(receipt_id)
    except NotFoundException as exc:
        messages.error(request, str(exc))
        return redirect("receipt_list")

    if scope["assigned_site_ids"] is not None and receipt.warehouse_id not in scope["assigned_site_ids"]:
        messages.error(request, "You do not have access to this receipt site.")
        return redirect("receipt_list")

    header_initial = {
        "supplier": receipt.supplier,
        "warehouse": receipt.warehouse,
        "source_type": receipt.source_type,
        "receipt_date": receipt.receipt_date,
        "notes": receipt.notes,
    }

    sites_qs = switchable_sites_for_user(request.user)
    suppliers_qs = Supplier.objects.order_by("name")
    if scope["active_site_id"]:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id=scope["active_site_id"]).distinct()
    elif scope["assigned_site_ids"] is not None:
        suppliers_qs = suppliers_qs.filter(supplier_sites__site_id__in=scope["assigned_site_ids"]).distinct()

    header_form = ReceiptHeaderEditForm(
        initial=header_initial,
        supplier_queryset=suppliers_qs,
        warehouse_queryset=sites_qs,
    )
    line_form = ReceiptLineEditForm()
    record_form = ReceiptRecordForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "edit_header":
            header_form = ReceiptHeaderEditForm(
                request.POST,
                request.FILES,
                supplier_queryset=suppliers_qs,
                warehouse_queryset=sites_qs,
            )
            if header_form.is_valid():
                try:
                    receipt_service.edit_receipt_header(
                        receipt_id=receipt.id,
                        editor=request.user,
                        reason=header_form.cleaned_data["reason"],
                        updates={
                            "supplier_id": header_form.cleaned_data["supplier"].id,
                            "warehouse_id": header_form.cleaned_data["warehouse"].id,
                            "source_type": header_form.cleaned_data["source_type"],
                            "receipt_date": header_form.cleaned_data["receipt_date"],
                            "notes": header_form.cleaned_data.get("notes") or "",
                            "scan_file": header_form.cleaned_data.get("scan_file") or receipt.scan_file,
                        },
                    )
                    messages.success(request, "Receipt header updated.")
                    logger.info("receipt.header_updated_view by=%s receipt_id=%s", request.user.username, receipt.id)
                    return redirect("receipt_detail", receipt_id=receipt.id)
                except ValidationException as exc:
                    header_form.add_error(None, str(exc))

        elif action == "upsert_line":
            line_form = ReceiptLineEditForm(request.POST)
            if line_form.is_valid():
                try:
                    line_id = line_form.cleaned_data.get("line_id")
                    receipt_service.upsert_line(
                        receipt_id=receipt.id,
                        editor=request.user,
                        reason=line_form.cleaned_data["reason"],
                        line_id=int(line_id) if line_id else None,
                        item_id=line_form.cleaned_data["item"].id,
                        quantity=line_form.cleaned_data["quantity"],
                        unit_price=float(line_form.cleaned_data["unit_price"]),
                    )
                    messages.success(request, "Receipt line saved.")
                    logger.info("receipt.line_saved_view by=%s receipt_id=%s", request.user.username, receipt.id)
                    return redirect("receipt_detail", receipt_id=receipt.id)
                except (ValidationException, NotFoundException) as exc:
                    line_form.add_error(None, str(exc))

        elif action == "record_receipt":
            record_form = ReceiptRecordForm(request.POST)
            if record_form.is_valid():
                try:
                    receipt_service.record_receipt(
                        receipt_id=receipt.id,
                        editor=request.user,
                        reason=record_form.cleaned_data["reason"],
                    )
                    messages.success(request, "Receipt recorded successfully.")
                    logger.info("receipt.recorded_view by=%s receipt_id=%s", request.user.username, receipt.id)
                    return redirect("receipt_detail", receipt_id=receipt.id)
                except (ValidationException, NotFoundException) as exc:
                    record_form.add_error(None, str(exc))

    receipt = receipt_service.get_receipt(receipt_id)
    return render(
        request,
        "receipt/receipt_detail.html",
        {
            "receipt": receipt,
            "header_form": header_form,
            "line_form": line_form,
            "record_form": record_form,
            "edit_logs": receipt.edit_logs.select_related("editor").order_by("-edited_at")[:500],
        },
    )
