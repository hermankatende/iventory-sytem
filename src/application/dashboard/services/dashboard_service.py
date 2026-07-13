from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone

from src.infrastructure.persistence.models import Expense, Invoice, LoginHistory, Payment, Receipt, UserActivityLog
from src.infrastructure.persistence.repositories.inventory_repository import DjangoInventoryRepository
from src.shared.utils.site_context import apply_site_scope


class DashboardService:
    def __init__(self):
        self.inventory_repository = DjangoInventoryRepository()

    def _today(self):
        return timezone.localdate()

    def _supplier_balance_total(self, *, assigned_site_ids=None, active_site_id=None) -> float:
        invoice_qs = apply_site_scope(
            Invoice.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        payment_qs = apply_site_scope(
            Payment.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        invoiced = invoice_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        paid = payment_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return float(invoiced - paid)

    def _inventory_trend(self, days: int = 30, *, assigned_site_ids=None, active_site_id=None) -> dict:
        end = self._today()
        start = end - timedelta(days=days - 1)

        per_day = defaultdict(int)
        rows = self.inventory_repository.get_inventory_history(
            warehouse_id=active_site_id if active_site_id else None,
        )
        for row in rows:
            if assigned_site_ids is not None and row.get("warehouse_id") not in assigned_site_ids:
                continue
            created_at = row.get("created_at")
            if not created_at:
                continue
            day = created_at.date()
            if start <= day <= end:
                per_day[str(day)] += int(row.get("delta", 0))

        labels = []
        values = []
        running = 0
        cursor = start
        while cursor <= end:
            key = str(cursor)
            running += per_day.get(key, 0)
            labels.append(key)
            values.append(running)
            cursor += timedelta(days=1)

        return {"labels": labels, "values": values}

    def _monthly_expenses(self, months: int = 12, *, assigned_site_ids=None, active_site_id=None) -> dict:
        today = self._today()
        expense_qs = apply_site_scope(
            Expense.objects.filter(date__lte=today),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        rows = (
            expense_qs
            .values("date__year", "date__month")
            .annotate(total=Sum("amount"))
            .order_by("date__year", "date__month")
        )
        labels = [f"{r['date__year']}-{int(r['date__month']):02d}" for r in rows][-months:]
        values = [float(r["total"] or 0) for r in rows][-months:]
        return {"labels": labels, "values": values}

    def dashboard_payload(self, *, activity_page: int = 1, login_page: int = 1, assigned_site_ids=None, active_site_id=None) -> dict:
        today = self._today()

        stock_rows = self.inventory_repository.list_current_stock(warehouse_id=active_site_id if active_site_id else None)
        if assigned_site_ids is not None:
            stock_rows = [row for row in stock_rows if row.get("warehouse_id") in assigned_site_ids]
        low_stock = [row for row in stock_rows if row.get("is_low_stock")]
        inventory_value = sum(float(row.get("valuation", 0)) for row in stock_rows)

        activity_qs = UserActivityLog.objects.select_related("user").order_by("-created_at")
        login_qs = LoginHistory.objects.select_related("user").order_by("-created_at")

        activity_page_obj = Paginator(activity_qs, 10).get_page(activity_page)
        login_page_obj = Paginator(login_qs, 10).get_page(login_page)

        expense_today_qs = apply_site_scope(
            Expense.objects.filter(date=today),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        receipts_today_qs = apply_site_scope(
            Receipt.objects.filter(receipt_date=today),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        payments_today_qs = apply_site_scope(
            Payment.objects.filter(payment_date=today),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )

        return {
            "cards": {
                "todays_expenses": float(expense_today_qs.aggregate(total=Sum("amount"))["total"] or 0),
                "current_inventory_value": inventory_value,
                "outstanding_supplier_balances": self._supplier_balance_total(
                    assigned_site_ids=assigned_site_ids,
                    active_site_id=active_site_id,
                ),
                "low_stock": len(low_stock),
                "receipts_today": receipts_today_qs.count(),
                "payments_today": payments_today_qs.count(),
            },
            "charts": {
                "monthly_expenses": self._monthly_expenses(
                    assigned_site_ids=assigned_site_ids,
                    active_site_id=active_site_id,
                ),
                "inventory_trend": self._inventory_trend(
                    assigned_site_ids=assigned_site_ids,
                    active_site_id=active_site_id,
                ),
            },
            "activity_page_obj": activity_page_obj,
            "login_page_obj": login_page_obj,
        }
