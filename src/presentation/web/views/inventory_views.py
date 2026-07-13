import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.application.inventory.services.catalog_service import ProductCatalogService
from src.application.inventory.services.inventory_service import InventoryService
from src.infrastructure.persistence.models import BatchOperation, InventoryTransaction, Product, ProductCategory, StockMovement, Warehouse
from src.infrastructure.persistence.repositories.inventory_repository import DjangoInventoryRepository
from src.presentation.web.permissions import require_permission, require_role
from src.presentation.web.forms.inventory_forms import (
    BatchOperationForm,
    InventoryTransactionForm,
    InventoryFilterForm,
    ProductCategoryForm,
    ProductRegistrationForm,
    StockAdjustmentForm,
    StockInOutForm,
    TransferForm,
)
from src.shared.utils.app_logger import get_app_logger
from src.shared.utils.site_context import site_scope_from_request, switchable_sites_for_user


catalog_service = ProductCatalogService()
inventory_service = InventoryService(DjangoInventoryRepository())
logger = get_app_logger("web.inventory")


@login_required
@require_permission("persistence.add_item")
@require_http_methods(["GET", "POST"])
def product_registration_view(request):
    form = ProductRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            catalog_service.register_product(
                sku=data["sku"],
                name=data["name"],
                reorder_level=data["reorder_level"],
                unit_cost=float(data["unit_cost"]),
                product_code=data["product_code"],
                category_id=data["category_id"].id if data["category_id"] else None,
                barcode=data.get("barcode", ""),
                unit_of_measure=data.get("unit_of_measure") or "unit",
            )
            messages.success(request, "Product saved successfully.")
            logger.info("inventory.product_saved by=%s sku=%s", request.user.username, data["sku"])
            return redirect("inventory_products")
        except ValidationException as exc:
            form.add_error(None, str(exc))

    products = catalog_service.search_products(
        search=request.GET.get("search", "").strip(),
        category_id=int(request.GET.get("category_id")) if request.GET.get("category_id", "").isdigit() else None,
    )
    categories = ProductCategory.objects.order_by("name")
    return render(
        request,
        "inventory/product_registration.html",
        {
            "form": form,
            "products": products,
            "categories": categories,
        },
    )


@login_required
@require_permission("persistence.add_productcategory")
@require_http_methods(["GET", "POST"])
def product_category_view(request):
    form = ProductCategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            catalog_service.register_category(
                name=form.cleaned_data["name"],
                description=form.cleaned_data.get("description", ""),
            )
            messages.success(request, "Category saved successfully.")
            logger.info("inventory.category_saved by=%s name=%s", request.user.username, form.cleaned_data["name"])
            return redirect("inventory_categories")
        except ValidationException as exc:
            form.add_error(None, str(exc))

    categories = ProductCategory.objects.order_by("name")
    return render(request, "inventory/product_categories.html", {"form": form, "categories": categories})


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["POST"])
def stock_in_view(request):
    scope = site_scope_from_request(request)
    form = StockInOutForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid stock-in input.")
        return redirect("inventory_current_stock")

    warehouse = form.cleaned_data["warehouse_id"]
    if scope["assigned_site_ids"] is not None and warehouse.id not in scope["assigned_site_ids"]:
        messages.error(request, "You are not assigned to this site.")
        return redirect("inventory_current_stock")
    try:
        inventory_service.stock_in(
            item_id=form.cleaned_data["item_id"],
            warehouse_id=warehouse.id,
            qty=form.cleaned_data["qty"],
            reason=form.cleaned_data.get("reason") or "Stock In",
        )
        messages.success(request, "Stock in completed.")
        logger.info("inventory.stock_in by=%s item=%s warehouse=%s qty=%s", request.user.username, form.cleaned_data["item_id"], warehouse.id, form.cleaned_data["qty"])
    except Exception as exc:  # noqa: BLE001
        messages.error(request, str(exc))
    return redirect("inventory_current_stock")


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["POST"])
def stock_out_view(request):
    scope = site_scope_from_request(request)
    form = StockInOutForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid stock-out input.")
        return redirect("inventory_current_stock")

    warehouse = form.cleaned_data["warehouse_id"]
    if scope["assigned_site_ids"] is not None and warehouse.id not in scope["assigned_site_ids"]:
        messages.error(request, "You are not assigned to this site.")
        return redirect("inventory_current_stock")
    try:
        inventory_service.stock_out(
            item_id=form.cleaned_data["item_id"],
            warehouse_id=warehouse.id,
            qty=form.cleaned_data["qty"],
            reason=form.cleaned_data.get("reason") or "Stock Out",
        )
        messages.success(request, "Stock out completed.")
        logger.info("inventory.stock_out by=%s item=%s warehouse=%s qty=%s", request.user.username, form.cleaned_data["item_id"], warehouse.id, form.cleaned_data["qty"])
    except Exception as exc:  # noqa: BLE001
        messages.error(request, str(exc))
    return redirect("inventory_current_stock")


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["POST"])
def transfer_between_sites_view(request):
    scope = site_scope_from_request(request)
    form = TransferForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid transfer input.")
        return redirect("inventory_current_stock")

    source = form.cleaned_data["source_warehouse_id"]
    destination = form.cleaned_data["destination_warehouse_id"]
    if scope["assigned_site_ids"] is not None:
        if source.id not in scope["assigned_site_ids"] or destination.id not in scope["assigned_site_ids"]:
            messages.error(request, "You are not assigned to one or more selected sites.")
            return redirect("inventory_current_stock")
    try:
        inventory_service.transfer_between_sites(
            item_id=form.cleaned_data["item_id"],
            source_warehouse_id=source.id,
            destination_warehouse_id=destination.id,
            qty=form.cleaned_data["qty"],
            reason=form.cleaned_data.get("reason") or "Site Transfer",
        )
        messages.success(request, "Transfer completed.")
        logger.info("inventory.transfer by=%s item=%s src=%s dst=%s qty=%s", request.user.username, form.cleaned_data["item_id"], source.id, destination.id, form.cleaned_data["qty"])
    except Exception as exc:  # noqa: BLE001
        messages.error(request, str(exc))
    return redirect("inventory_current_stock")


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["POST"])
def stock_adjustment_view(request):
    scope = site_scope_from_request(request)
    form = StockAdjustmentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid adjustment input.")
        return redirect("inventory_current_stock")

    warehouse = form.cleaned_data["warehouse_id"]
    if scope["assigned_site_ids"] is not None and warehouse.id not in scope["assigned_site_ids"]:
        messages.error(request, "You are not assigned to this site.")
        return redirect("inventory_current_stock")
    try:
        inventory_service.adjust_stock(
            item_id=form.cleaned_data["item_id"],
            warehouse_id=warehouse.id,
            delta=form.cleaned_data["delta"],
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Adjustment completed.")
        logger.info("inventory.adjust by=%s item=%s warehouse=%s delta=%s", request.user.username, form.cleaned_data["item_id"], warehouse.id, form.cleaned_data["delta"])
    except Exception as exc:  # noqa: BLE001
        messages.error(request, str(exc))
    return redirect("inventory_current_stock")


@login_required
@require_permission("persistence.view_stocklevel")
@require_http_methods(["GET"])
def current_stock_view(request):
    scope = site_scope_from_request(request)
    filter_form = InventoryFilterForm(request.GET or None)
    filter_form.is_valid()
    cleaned = getattr(filter_form, "cleaned_data", {})

    selected_site_id = cleaned.get("warehouse_id").id if cleaned.get("warehouse_id") else None
    if not selected_site_id:
        selected_site_id = scope["active_site_id"]

    rows = inventory_service.get_current_stock(
        search=(cleaned.get("search") or "") if cleaned else "",
        category_id=cleaned.get("category_id").id if cleaned.get("category_id") else None,
        warehouse_id=selected_site_id,
    )
    if selected_site_id is None and scope["assigned_site_ids"] is not None:
        rows = [row for row in rows if row.get("warehouse_id") in scope["assigned_site_ids"]]

    valuation = inventory_service.get_stock_valuation()
    if scope["active_site_id"] is None and scope["assigned_site_ids"] is not None:
        valuation["per_warehouse"] = {
            name: value
            for name, value in valuation["per_warehouse"].items()
            if name in set(s.name for s in switchable_sites_for_user(request.user))
        }
        valuation["total_valuation"] = sum(valuation["per_warehouse"].values())
    low_stock = inventory_service.get_low_stock_alerts()
    if scope["assigned_site_ids"] is not None:
        low_stock = [row for row in low_stock if row.get("warehouse_id") in scope["assigned_site_ids"]]

    return render(
        request,
        "inventory/current_stock.html",
        {
            "filter_form": filter_form,
            "rows": rows,
            "valuation": valuation,
            "low_stock": low_stock,
            "stock_in_form": StockInOutForm(),
            "stock_out_form": StockInOutForm(),
            "adjust_form": StockAdjustmentForm(),
            "transfer_form": TransferForm(),
            "warehouses": switchable_sites_for_user(request.user),
        },
    )


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["GET", "POST"])
def inventory_transaction_view(request):
    scope = site_scope_from_request(request)
    form = InventoryTransactionForm(
        request.POST or None,
        site_queryset=switchable_sites_for_user(request.user),
        product_queryset=Product.objects.select_related("item").order_by("product_name", "product_code"),
    )

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        site = data["site"]
        if scope["assigned_site_ids"] is not None and site.id not in scope["assigned_site_ids"]:
            form.add_error("site", "You are not assigned to this site.")
        else:
            quantity = data["quantity"]
            if data["transaction_type"] in {"SITE_ISSUE", "TRANSFER_OUT"} and quantity > 0:
                quantity = -quantity
            elif data["transaction_type"] in {"PURCHASE_RECEIPT", "TRANSFER_IN"} and quantity < 0:
                quantity = abs(quantity)

            unit_cost = data.get("unit_cost") or data["product"].item.unit_cost
            InventoryTransaction.objects.create(
                site=site,
                product=data["product"],
                transaction_type=data["transaction_type"],
                quantity=quantity,
                unit_cost=unit_cost,
                date=data["date"],
                reference_number=(data.get("reference_number") or "").strip(),
                entered_by=request.user,
                remarks=data.get("remarks") or "",
            )
            messages.success(request, "Inventory transaction saved.")
            return redirect("inventory_transaction_entry")

    recent_transactions = InventoryTransaction.objects.select_related("site", "product", "entered_by").order_by("-date", "-id")
    if scope["assigned_site_ids"] is not None:
        recent_transactions = recent_transactions.filter(site_id__in=scope["assigned_site_ids"])
    recent_transactions = recent_transactions[:50]

    return render(
        request,
        "inventory/inventory_transaction.html",
        {
            "form": form,
            "recent_transactions": recent_transactions,
        },
    )


@login_required
@require_role("WarehouseOperator")
@require_http_methods(["GET", "POST"])
def batch_operations_view(request):
    form = BatchOperationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            operations = json.loads(form.cleaned_data["operations_json"])
            if not isinstance(operations, list):
                raise ValidationException("Operations must be a JSON list")

            with transaction.atomic():
                batch_id = inventory_service.process_batch_adjustments(
                    operation_type=form.cleaned_data["operation_type"],
                    operations=operations,
                    reason=form.cleaned_data.get("reason") or "Batch Operation",
                )
            messages.success(request, f"Batch processed successfully: {batch_id}")
            logger.info("inventory.batch_processed by=%s batch_id=%s op=%s", request.user.username, batch_id, form.cleaned_data["operation_type"])
            return redirect("inventory_batch_operations")
        except (json.JSONDecodeError, ValidationException, KeyError, TypeError, ValueError) as exc:
            form.add_error("operations_json", str(exc))

    batches = BatchOperation.objects.order_by("-created_at")[:200]
    return render(request, "inventory/batch_operations.html", {"form": form, "batches": batches})


@login_required
@require_permission("persistence.view_stockmovement")
@require_http_methods(["GET"])
def inventory_history_view(request):
    scope = site_scope_from_request(request)
    item_id = int(request.GET.get("item_id")) if request.GET.get("item_id", "").isdigit() else None
    warehouse_id = int(request.GET.get("warehouse_id")) if request.GET.get("warehouse_id", "").isdigit() else None
    if not warehouse_id:
        warehouse_id = scope["active_site_id"]
    if warehouse_id and scope["assigned_site_ids"] is not None and warehouse_id not in scope["assigned_site_ids"]:
        warehouse_id = None
    history = inventory_service.get_inventory_history(item_id=item_id, warehouse_id=warehouse_id)
    if warehouse_id is None and scope["assigned_site_ids"] is not None:
        history = [row for row in history if row.get("warehouse_id") in scope["assigned_site_ids"]]
    return render(request, "inventory/inventory_history.html", {"history": history})


@login_required
@require_permission("persistence.view_stocklevel")
@require_http_methods(["GET"])
def stock_reports_view(request):
    scope = site_scope_from_request(request)
    rows = inventory_service.get_current_stock(warehouse_id=scope["active_site_id"] if scope["active_site_id"] else None)
    if scope["active_site_id"] is None and scope["assigned_site_ids"] is not None:
        rows = [row for row in rows if row.get("warehouse_id") in scope["assigned_site_ids"]]

    low_stock = [row for row in rows if row.get("is_low_stock")]
    total_valuation = sum(float(row.get("valuation", 0)) for row in rows)

    reports = {
        "summary": {
            "total_products": len({entry["item_id"] for entry in rows}),
            "total_stock_rows": len(rows),
            "low_stock_count": len(low_stock),
            "total_valuation": total_valuation,
        },
        "low_stock": low_stock,
        "valuation": {
            "total_valuation": total_valuation,
            "per_warehouse": {},
        },
        "current_stock": rows,
    }

    history = inventory_service.get_inventory_history(warehouse_id=scope["active_site_id"] if scope["active_site_id"] else None)
    if scope["active_site_id"] is None and scope["assigned_site_ids"] is not None:
        history = [row for row in history if row.get("warehouse_id") in scope["assigned_site_ids"]]

    cards = {
        "total_products": reports["summary"]["total_products"],
        "total_valuation": reports["summary"]["total_valuation"],
        "low_stock_count": reports["summary"]["low_stock_count"],
        "stock_in_count": sum(1 for row in history[:100] if row["movement_type"] == "IN"),
        "stock_out_count": sum(1 for row in history[:100] if row["movement_type"] == "OUT"),
        "transfer_count": sum(1 for row in history[:100] if row["movement_type"] == "TRANSFER"),
    }

    valuation_by_site = {}
    for row in rows:
        valuation_by_site[row["warehouse"]] = valuation_by_site.get(row["warehouse"], 0) + float(row.get("valuation", 0))
    charts = {
        "valuation_by_site": {
            "labels": list(valuation_by_site.keys()),
            "values": list(valuation_by_site.values()),
        }
    }

    movement_breakdown_qs = StockMovement.objects.all()
    if scope["active_site_id"]:
        movement_breakdown_qs = movement_breakdown_qs.filter(warehouse_id=scope["active_site_id"])
    elif scope["assigned_site_ids"] is not None:
        movement_breakdown_qs = movement_breakdown_qs.filter(warehouse_id__in=scope["assigned_site_ids"])

    movement_breakdown = (
        movement_breakdown_qs.values("movement_type")
        .annotate(total=Count("id"))
        .order_by("movement_type")
    )

    return render(
        request,
        "inventory/stock_reports.html",
        {
            "reports": reports,
            "cards": cards,
            "charts": charts,
            "movement_breakdown": list(movement_breakdown),
        },
    )


@login_required
@require_permission("persistence.view_stocklevel")
@require_http_methods(["GET"])
def site_stock_view(request):
    scope = site_scope_from_request(request)
    stock_qs = (
        InventoryTransaction.objects.select_related("site", "product")
        .values("site_id", "site__name", "product_id", "product__product_code", "product__product_name")
        .annotate(quantity_on_hand=Sum("quantity"))
        .order_by("site__name", "product__product_name", "product__product_code")
    )

    if scope["active_site_id"]:
        stock_qs = stock_qs.filter(site_id=scope["active_site_id"])
    elif scope["assigned_site_ids"] is not None:
        stock_qs = stock_qs.filter(site_id__in=scope["assigned_site_ids"])

    return render(
        request,
        "inventory/site_stock.html",
        {
            "rows": list(stock_qs),
        },
    )
