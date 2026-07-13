"""Cross-module reporting service.

Provides filterable report datasets for operational and financial modules.
"""

from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.db.models.functions import ExtractMonth, ExtractYear

from src.application.inventory.services.inventory_service import InventoryService
from src.infrastructure.persistence.models import (
    Expense,
    Invoice,
    Payment,
    Product,
    Receipt,
    ReceiptEditLog,
    StockLevel,
    StockMovement,
    Supplier,
    Warehouse,
)
from src.infrastructure.persistence.repositories.inventory_repository import DjangoInventoryRepository
from src.shared.utils.site_context import apply_site_scope


class ReportService:
    """Build report payloads for UI and export layers."""

    def __init__(self):
        self.inventory_service = InventoryService(DjangoInventoryRepository())

    def _date_filter(self, queryset, *, field_name: str, start_date=None, end_date=None):
        """Apply start/end date filters to a queryset field."""
        if start_date:
            queryset = queryset.filter(**{f"{field_name}__gte": start_date})
        if end_date:
            queryset = queryset.filter(**{f"{field_name}__lte": end_date})
        return queryset

    def _scope(self, queryset, *, field_name: str, assigned_site_ids=None, active_site_id=None, explicit_site_id=None):
        return apply_site_scope(
            queryset,
            field_name=field_name,
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=explicit_site_id,
        )

    def inventory_report(self, *, site_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        resolved_site_id = site_id or active_site_id
        rows = self.inventory_service.get_current_stock(warehouse_id=resolved_site_id)
        if resolved_site_id is None and assigned_site_ids is not None:
            rows = [row for row in rows if row.get("warehouse_id") in assigned_site_ids]
        return rows

    def suppliers_report(self, *, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = Supplier.objects.all()
        if assigned_site_ids is not None:
            supplier_ids = set(
                self._scope(Receipt.objects.all(), field_name="warehouse_id", assigned_site_ids=assigned_site_ids, active_site_id=active_site_id)
                .values_list("supplier_id", flat=True)
            )
            queryset = queryset.filter(id__in=supplier_ids)

        return list(
            queryset.annotate(
                receipt_count=Count("receipts"),
                invoice_count=Count("invoices"),
                payment_count=Count("payments"),
            )
            .values("id", "name", "email", "phone", "address", "receipt_count", "invoice_count", "payment_count")
            .order_by("name")
        )

    def receipts_report(self, *, site_id=None, supplier_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Receipt.objects.select_related("supplier", "warehouse"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        queryset = self._date_filter(queryset, field_name="receipt_date", start_date=start_date, end_date=end_date)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return list(
            queryset.values(
                "receipt_number",
                "receipt_date",
                "source_type",
                "is_recorded",
                "supplier__name",
                "warehouse__name",
            ).order_by("-receipt_date")
        )

    def invoices_report(self, *, site_id=None, supplier_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Invoice.objects.select_related("supplier", "site"),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        queryset = self._date_filter(queryset, field_name="invoice_date", start_date=start_date, end_date=end_date)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return list(queryset.values("invoice_number", "invoice_date", "due_date", "amount", "status", "supplier__name", "site__name").order_by("-invoice_date"))

    def payments_report(self, *, site_id=None, supplier_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Payment.objects.select_related("supplier", "site", "invoice"),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        queryset = self._date_filter(queryset, field_name="payment_date", start_date=start_date, end_date=end_date)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return list(queryset.values("payment_date", "amount", "method", "reference", "supplier__name", "site__name", "invoice__invoice_number").order_by("-payment_date"))

    def expenses_report(self, *, site_id=None, supplier_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Expense.objects.select_related("category", "site", "supplier"),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        queryset = self._date_filter(queryset, field_name="date", start_date=start_date, end_date=end_date)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return list(queryset.values("date", "amount", "description", "category__name", "site__name", "supplier__name").order_by("-date"))

    def sites_report(self, *, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Warehouse.objects.all(),
            field_name="id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        return list(
            queryset.annotate(
                expense_count=Count("expenses"),
                receipt_count=Count("receipts"),
                invoice_count=Count("invoices"),
                payment_count=Count("payments"),
            )
            .values("id", "code", "name", "expense_count", "receipt_count", "invoice_count", "payment_count")
            .order_by("name")
        )

    def products_report(self) -> list[dict]:
        return list(
            Product.objects.select_related("item", "category")
            .values(
                "item__name",
                "item__sku",
                "product_code",
                "barcode",
                "category__name",
                "item__unit_cost",
                "item__reorder_level",
            )
            .order_by("item__name")
        )

    def stock_movement_report(self, *, site_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            StockMovement.objects.select_related("item", "warehouse"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        queryset = self._date_filter(queryset, field_name="created_at__date", start_date=start_date, end_date=end_date)
        return list(
            queryset.values("created_at", "movement_type", "delta", "reason", "reference", "item__name", "warehouse__name")
            .order_by("-created_at")
        )

    def supplier_balance_report(self, *, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        receipted_totals = defaultdict(Decimal)
        invoice_totals = defaultdict(Decimal)
        payment_totals = defaultdict(Decimal)

        for row in (
            self._scope(
                Receipt.objects.all(),
                field_name="warehouse_id",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            )
            .values("supplier_id")
            .annotate(total=Coalesce(Sum("total_amount"), Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))))
        ):
            receipted_totals[row["supplier_id"]] = row["total"] or Decimal("0")

        for row in self._scope(
            Invoice.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        ).values("supplier_id").annotate(total=Sum("amount")):
            invoice_totals[row["supplier_id"]] = row["total"] or Decimal("0")

        for row in self._scope(
            Payment.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        ).values("supplier_id").annotate(total=Sum("amount")):
            payment_totals[row["supplier_id"]] = row["total"] or Decimal("0")

        rows = []
        for supplier in Supplier.objects.all().order_by("name"):
            receipted = receipted_totals[supplier.id]
            invoiced = invoice_totals[supplier.id]
            gross = receipted + invoiced
            paid = payment_totals[supplier.id]
            balance = gross - paid
            rows.append(
                {
                    "supplier": supplier.name,
                    "receipted": float(receipted),
                    "invoiced": float(invoiced),
                    "gross": float(gross),
                    "paid": float(paid),
                    "balance": float(balance),
                }
            )
        return rows

    def expenses_time_grouped_report(self, *, start_date=None, end_date=None, granularity: str = "daily", assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Expense.objects.select_related("site", "category"),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        queryset = self._date_filter(queryset, field_name="date", start_date=start_date, end_date=end_date)

        if granularity == "weekly":
            rows = (
                queryset.values("date", "site__name", "category__name")
                .annotate(total=Sum("amount"))
                .order_by("date", "site__name", "category__name")
            )
            return [
                {
                    "period": f"{row['date'].isocalendar().year}-W{row['date'].isocalendar().week:02d}",
                    "site": row["site__name"],
                    "category": row["category__name"],
                    "total": float(row["total"] or 0),
                }
                for row in rows
            ]

        if granularity == "monthly":
            rows = (
                queryset.annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
                .values("year", "month", "site__name", "category__name")
                .annotate(total=Sum("amount"))
                .order_by("year", "month", "site__name", "category__name")
            )
            return [
                {
                    "period": f"{row['year']}-{row['month']:02d}",
                    "site": row["site__name"],
                    "category": row["category__name"],
                    "total": float(row["total"] or 0),
                }
                for row in rows
            ]

        rows = (
            queryset.values("date", "site__name", "category__name")
            .annotate(total=Sum("amount"))
            .order_by("date", "site__name", "category__name")
        )
        return [
            {
                "period": str(row["date"]),
                "site": row["site__name"],
                "category": row["category__name"],
                "total": float(row["total"] or 0),
            }
            for row in rows
        ]

    def products_bought_report(self, *, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        lines = self._scope(
            Receipt.objects.select_related("supplier").prefetch_related("lines__item", "lines__product"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        lines = self._date_filter(lines, field_name="receipt_date", start_date=start_date, end_date=end_date)

        totals: dict[str, dict] = {}
        for receipt in lines:
            for line in receipt.lines.all():
                key = f"product:{line.product_id}" if line.product_id else f"item:{line.item_id}"
                name = (
                    line.product.product_name
                    if line.product_id and line.product.product_name
                    else (line.product.item.name if line.product_id else line.item.name)
                )
                row = totals.setdefault(
                    key,
                    {
                        "product_id": line.product_id,
                        "item_id": line.item_id,
                        "product_name": name,
                        "quantity": 0,
                        "total_spend": Decimal("0"),
                    },
                )
                row["quantity"] += line.quantity
                row["total_spend"] += line.total

        return [
            {
                "product_id": row["product_id"],
                "item_id": row["item_id"],
                "product_name": row["product_name"],
                "quantity": row["quantity"],
                "total_spend": float(row["total_spend"]),
            }
            for row in totals.values()
        ]

    def outstanding_supplier_balances_report(self, *, supplier_id=None, site_id=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Receipt.objects.select_related("supplier", "warehouse"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        receipt_totals = defaultdict(Decimal)
        payment_totals = defaultdict(Decimal)

        for row in queryset.values("supplier_id", "warehouse_id").annotate(total=Sum("total_amount")):
            key = (row["supplier_id"], row["warehouse_id"])
            receipt_totals[key] = row["total"] or Decimal("0")

        payments = self._scope(
            Payment.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        if supplier_id:
            payments = payments.filter(supplier_id=supplier_id)

        for row in payments.values("supplier_id", "site_id").annotate(total=Sum("amount")):
            key = (row["supplier_id"], row["site_id"])
            payment_totals[key] = row["total"] or Decimal("0")

        rows = []
        for (sid, wid), receipt_total in receipt_totals.items():
            paid_total = payment_totals[(sid, wid)]
            balance = receipt_total - paid_total
            supplier_name = Supplier.objects.filter(id=sid).values_list("name", flat=True).first() or ""
            site_name = Warehouse.objects.filter(id=wid).values_list("name", flat=True).first() or ""
            rows.append(
                {
                    "supplier_id": sid,
                    "supplier": supplier_name,
                    "site_id": wid,
                    "site": site_name,
                    "receipts_total": float(receipt_total),
                    "payments_total": float(paid_total),
                    "outstanding_balance": float(balance),
                }
            )
        return rows

    def site_expense_summary_report(self, *, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Expense.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        queryset = self._date_filter(queryset, field_name="date", start_date=start_date, end_date=end_date)
        return list(
            queryset.values("site_id", "site__name")
            .annotate(total_expense=Sum("amount"), entries=Count("id"))
            .order_by("site__name")
        )

    def receipt_history_log_report(self, *, receipt_id=None, start_date=None, end_date=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = ReceiptEditLog.objects.select_related("receipt", "editor")
        queryset = queryset.filter(
            receipt_id__in=self._scope(
                Receipt.objects.values("id"),
                field_name="warehouse_id",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            )
        )
        queryset = self._date_filter(queryset, field_name="edited_at__date", start_date=start_date, end_date=end_date)
        if receipt_id:
            queryset = queryset.filter(receipt_id=receipt_id)
        return list(
            queryset.values(
                "receipt_id",
                "receipt__receipt_number",
                "field_name",
                "old_value",
                "new_value",
                "reason",
                "editor__username",
                "edited_at",
            ).order_by("-edited_at")
        )

    def top_suppliers_report(self, limit: int = 10) -> list[dict]:
        rows = (
            Invoice.objects.values("supplier__name")
            .annotate(total_invoice=Sum("amount"), invoice_count=Count("id"))
            .order_by("-total_invoice")[:limit]
        )
        return list(rows)

    def monthly_expenses_report(self, *, year=None, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Expense.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        if year:
            queryset = queryset.filter(date__year=year)
        return list(
            queryset.annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
            .values("year", "month")
            .annotate(total=Sum("amount"))
            .order_by("year", "month")
        )

    def yearly_expenses_report(self, *, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        queryset = self._scope(
            Expense.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        return list(
            queryset.annotate(year=ExtractYear("date"))
            .values("year")
            .annotate(total=Sum("amount"))
            .order_by("year")
        )

    def inventory_valuation_report(self, *, assigned_site_ids=None, active_site_id=None) -> list[dict]:
        rows = StockLevel.objects.select_related("warehouse", "item")
        if active_site_id:
            rows = rows.filter(warehouse_id=active_site_id)
        elif assigned_site_ids is not None:
            rows = rows.filter(warehouse_id__in=assigned_site_ids)
        per_site = defaultdict(Decimal)
        for row in rows:
            per_site[row.warehouse.name] += Decimal(row.qty_on_hand) * row.item.unit_cost
        return [{"site": site, "valuation": float(total)} for site, total in per_site.items()]

    def generate_report(
        self,
        report_type: str,
        *,
        site_id=None,
        supplier_id=None,
        start_date=None,
        end_date=None,
        assigned_site_ids=None,
        active_site_id=None,
    ) -> dict:
        """Generate a normalized report response by report key."""
        dispatch = {
            "inventory": lambda: self.inventory_report(
                site_id=site_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "suppliers": lambda: self.suppliers_report(assigned_site_ids=assigned_site_ids, active_site_id=active_site_id),
            "receipts": lambda: self.receipts_report(
                site_id=site_id,
                supplier_id=supplier_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "invoices": lambda: self.invoices_report(
                site_id=site_id,
                supplier_id=supplier_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "payments": lambda: self.payments_report(
                site_id=site_id,
                supplier_id=supplier_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "expenses": lambda: self.expenses_report(
                site_id=site_id,
                supplier_id=supplier_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "sites": lambda: self.sites_report(assigned_site_ids=assigned_site_ids, active_site_id=active_site_id),
            "products": self.products_report,
            "current_stock": lambda: self.inventory_report(
                site_id=site_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "stock_movement": lambda: self.stock_movement_report(
                site_id=site_id,
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "supplier_balance": lambda: self.supplier_balance_report(
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "top_suppliers": self.top_suppliers_report,
            "monthly_expenses": lambda: self.monthly_expenses_report(
                year=start_date.year if start_date else None,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "yearly_expenses": lambda: self.yearly_expenses_report(
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "inventory_valuation": lambda: self.inventory_valuation_report(
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "expenses_daily": lambda: self.expenses_time_grouped_report(
                start_date=start_date,
                end_date=end_date,
                granularity="daily",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "expenses_weekly": lambda: self.expenses_time_grouped_report(
                start_date=start_date,
                end_date=end_date,
                granularity="weekly",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "expenses_monthly": lambda: self.expenses_time_grouped_report(
                start_date=start_date,
                end_date=end_date,
                granularity="monthly",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "products_bought": lambda: self.products_bought_report(
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "outstanding_supplier_balances": lambda: self.outstanding_supplier_balances_report(
                supplier_id=supplier_id,
                site_id=site_id,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "site_expense_summary": lambda: self.site_expense_summary_report(
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
            "receipt_history_log": lambda: self.receipt_history_log_report(
                start_date=start_date,
                end_date=end_date,
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            ),
        }

        rows = dispatch.get(report_type, lambda: [])()
        return {
            "report_type": report_type,
            "rows": rows,
            "count": len(rows),
        }
