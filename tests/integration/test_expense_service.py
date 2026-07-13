"""Integration tests for expense service flows."""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from src.application.expenses.services.expense_service import ExpenseService
from src.infrastructure.persistence.models import Expense, ExpenseCategory, Supplier, Warehouse


class ExpenseServiceIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="expense_user", password="secret")
        self.warehouse = Warehouse.objects.create(code="SITE-B", name="Site B")
        self.supplier = Supplier.objects.create(name="Fuel Supplier", email="fuel@example.com")
        self.service = ExpenseService()
        self.service.ensure_default_categories()

    def test_create_expense_persists_row(self):
        category = ExpenseCategory.objects.first()

        expense = self.service.create_expense(
            category_id=category.id,
            site_id=self.warehouse.id,
            supplier_id=self.supplier.id,
            date=date.today(),
            amount=250.0,
            description="Fuel purchase",
            attachment=None,
            created_by=self.user,
        )

        self.assertTrue(Expense.objects.filter(id=expense.id).exists())
