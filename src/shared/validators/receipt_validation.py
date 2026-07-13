from src.application.common.exceptions.domain_exceptions import ValidationException


class ReceiptValidator:
    @staticmethod
    def validate_header(receipt_number: str, source_type: str) -> None:
        if not (receipt_number or "").strip():
            raise ValidationException("Receipt number is required.")
        if source_type not in {"SUPPLIER", "COMPANY"}:
            raise ValidationException("Source type must be SUPPLIER or COMPANY.")

    @staticmethod
    def validate_line(quantity: int, unit_price: float) -> None:
        if quantity <= 0:
            raise ValidationException("Quantity must be greater than zero.")
        if unit_price < 0:
            raise ValidationException("Unit price must be zero or positive.")

    @staticmethod
    def validate_reason(reason: str) -> None:
        if not (reason or "").strip():
            raise ValidationException("Reason is required.")
