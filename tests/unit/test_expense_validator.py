"""Unit tests for expense validation rules."""

from django.test import SimpleTestCase

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.shared.validators.expense_validation import ExpenseValidator


class ExpenseValidatorTests(SimpleTestCase):
    def test_validate_amount_rejects_zero(self):
        with self.assertRaises(ValidationException):
            ExpenseValidator.validate_amount(0)

    def test_validate_description_rejects_too_long(self):
        with self.assertRaises(ValidationException):
            ExpenseValidator.validate_description("x" * 2001)
