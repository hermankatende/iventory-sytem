"""Unit tests for receipt validation rules."""

from django.test import SimpleTestCase

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.shared.validators.receipt_validation import ReceiptValidator


class ReceiptValidatorTests(SimpleTestCase):
    def test_validate_header_rejects_empty_number(self):
        with self.assertRaises(ValidationException):
            ReceiptValidator.validate_header(receipt_number="", source_type="SUPPLIER")

    def test_validate_line_rejects_non_positive_quantity(self):
        with self.assertRaises(ValidationException):
            ReceiptValidator.validate_line(quantity=0, unit_price=10.0)

    def test_validate_reason_rejects_empty_reason(self):
        with self.assertRaises(ValidationException):
            ReceiptValidator.validate_reason("   ")
