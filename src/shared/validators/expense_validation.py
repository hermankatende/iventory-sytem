from src.application.common.exceptions.domain_exceptions import ValidationException


class ExpenseValidator:
    @staticmethod
    def validate_amount(amount: float) -> None:
        if amount <= 0:
            raise ValidationException("Amount must be greater than zero.")

    @staticmethod
    def validate_description(description: str) -> None:
        if len((description or "").strip()) > 2000:
            raise ValidationException("Description is too long.")
