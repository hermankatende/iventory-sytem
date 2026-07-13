"""Integration tests for receipt service workflows."""

from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from src.application.procurement.services.receipt_service import ReceiptService
from src.infrastructure.persistence.models import Item, Receipt, ReceiptLine, Supplier, Warehouse


@override_settings(ROOT_URLCONF="config.urls")
class ReceiptServiceIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret")
        self.supplier = Supplier.objects.create(name="Supplier A", email="a@example.com")
        self.warehouse = Warehouse.objects.create(code="SITE-A", name="Site A")
        self.item = Item.objects.create(sku="ITM-001", name="Cement", reorder_level=10, unit_cost=50)
        self.service = ReceiptService()

    def test_create_receipt_creates_header_and_lines(self):
        receipt = self.service.create_receipt(
            receipt_number="RCPT-1001",
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            source_type="SUPPLIER",
            receipt_date=date.today(),
            notes="Initial stock",
            scan_file=None,
            lines=[{"item_id": self.item.id, "quantity": 5, "unit_price": 47.5}],
            created_by=self.user,
        )

        self.assertTrue(Receipt.objects.filter(id=receipt.id).exists())
        self.assertEqual(ReceiptLine.objects.filter(receipt=receipt).count(), 1)

    def test_record_receipt_marks_recorded(self):
        receipt = self.service.create_receipt(
            receipt_number="RCPT-1002",
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            source_type="SUPPLIER",
            receipt_date=date.today(),
            notes="To record",
            scan_file=None,
            lines=[{"item_id": self.item.id, "quantity": 3, "unit_price": 49.0}],
            created_by=self.user,
        )

        self.service.record_receipt(receipt_id=receipt.id, editor=self.user, reason="Verified and accepted")
        receipt.refresh_from_db()
        self.assertTrue(receipt.is_recorded)
