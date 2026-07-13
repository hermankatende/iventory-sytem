"""Expense management service with validation and analytical summaries."""

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.infrastructure.persistence.models import Expense, ExpenseCategory
from src.shared.utils.site_context import apply_site_scope
from src.shared.utils.app_logger import get_app_logger
from src.shared.validators.expense_validation import ExpenseValidator


logger = get_app_logger("app.expenses")


class ExpenseService:
    DEFAULT_CATEGORIES = [
        ("BUYING_MATERIALS", "Buying Materials"),
        ("FUEL", "Fuel"),
        ("LABOUR", "Labour"),
        ("TRANSPORT", "Transport"),
        ("ACCOMMODATION", "Accommodation"),
        ("REPAIRS", "Repairs"),
        ("CONTRACTOR_PAYMENT", "Contractor Payment"),
        ("EQUIPMENT", "Equipment"),
        # Backward-compatible legacy value.
        ("CONTRACTOR_PAYMENTS", "Contractor Payments"),
        ("OTHER", "Other"),
    ]

    @transaction.atomic
    def ensure_default_categories(self) -> None:
        """Create standard expense categories if not present."""
        for code, name in self.DEFAULT_CATEGORIES:
            ExpenseCategory.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})

    @transaction.atomic
    def create_expense(
        self,
        *,
        category_id: int,
        site_id: int,
        supplier_id: int | None,
        date,
        amount: float,
        description: str,
        attachment,
        created_by,
    ) -> Expense:
        """Create a validated expense row."""
        self.ensure_default_categories()
        ExpenseValidator.validate_amount(amount=amount)
        ExpenseValidator.validate_description(description=description)

        category = ExpenseCategory.objects.filter(id=category_id, is_active=True).first()
        if not category:
            raise ValidationException("Invalid expense category.")

        expense = Expense.objects.create(
            category_id=category_id,
            site_id=site_id,
            supplier_id=supplier_id,
            date=date,
            amount=amount,
            description=(description or "").strip(),
            attachment=attachment,
            created_by=created_by,
        )
        logger.info("expense.created id=%s category=%s site=%s amount=%s", expense.id, expense.category.code, expense.site_id, expense.amount)
        return expense

    def list_expenses(
        self,
        *,
        start_date=None,
        end_date=None,
        site_id: int | None = None,
        supplier_id: int | None = None,
        category_id: int | None = None,
        assigned_site_ids=None,
        active_site_id=None,
    ):
        """Return filtered expense queryset for list/report screens."""
        queryset = apply_site_scope(
            Expense.objects.select_related("category", "site", "supplier").order_by("-date", "-created_at"),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
            explicit_site_id=site_id,
        )
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def monthly_totals(self, *, year: int | None = None, assigned_site_ids=None, active_site_id=None):
        """Aggregate monthly totals, optionally constrained by year."""
        queryset = apply_site_scope(
            Expense.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        if year:
            queryset = queryset.filter(date__year=year)

        rows = (
            queryset.annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
            .values("year", "month")
            .annotate(total=Sum("amount"))
            .order_by("year", "month")
        )
        return list(rows)

    def yearly_totals(self, *, assigned_site_ids=None, active_site_id=None):
        """Aggregate yearly expense totals."""
        queryset = apply_site_scope(
            Expense.objects.all(),
            field_name="site_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        rows = (
            queryset.annotate(year=ExtractYear("date"))
            .values("year")
            .annotate(total=Sum("amount"))
            .order_by("year")
        )
        return list(rows)
