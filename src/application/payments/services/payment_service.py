import json
from decimal import Decimal

from django.db import transaction

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.infrastructure.persistence.models import Payment, PaymentAllocation, Receipt
from src.shared.utils.site_context import apply_site_scope


class PaymentService:
    def outstanding_receipts_for_supplier(self, *, supplier_id: int, assigned_site_ids=None, active_site_id=None):
        receipts = apply_site_scope(
            Receipt.objects.filter(supplier_id=supplier_id).order_by("receipt_date", "id"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        result = []
        for receipt in receipts:
            allocated = (
                PaymentAllocation.objects.filter(receipt_id=receipt.id)
                .values_list("amount_allocated", flat=True)
            )
            total_allocated = sum(allocated, Decimal("0"))
            outstanding = Decimal(receipt.total_amount) - total_allocated
            if outstanding > 0:
                result.append(
                    {
                        "receipt_id": receipt.id,
                        "invoice_no": receipt.receipt_number,
                        "transaction_date": receipt.receipt_date.isoformat(),
                        "purchase_total": float(receipt.total_amount),
                        "payment_total": float(total_allocated),
                        "balance_outstanding": float(outstanding),
                    }
                )
        return result

    def parse_allocations_json(self, allocations_json: str):
        try:
            rows = json.loads(allocations_json or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationException("Invalid allocation data.") from exc

        if not isinstance(rows, list) or not rows:
            raise ValidationException("Select at least one receipt allocation.")

        normalized = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            receipt_id = int(row.get("receipt_id", 0))
            amount_allocated = Decimal(str(row.get("amount_allocated", 0)))
            if receipt_id <= 0:
                continue
            if amount_allocated <= 0:
                continue
            normalized.append({"receipt_id": receipt_id, "amount_allocated": amount_allocated})

        if not normalized:
            raise ValidationException("At least one positive allocation is required.")
        return normalized

    @transaction.atomic
    def create_payment_with_allocations(
        self,
        *,
        supplier_id: int,
        amount: Decimal,
        payment_date,
        method: str,
        description: str = "",
        reference_number: str,
        allocations: list[dict],
        site_id=None,
        assigned_site_ids=None,
        active_site_id=None,
    ) -> Payment:
        total_allocated = sum((row["amount_allocated"] for row in allocations), Decimal("0"))
        if total_allocated > amount:
            raise ValidationException("Allocated amount cannot exceed payment total.")

        payment = Payment.objects.create(
            supplier_id=supplier_id,
            site_id=site_id,
            amount=amount,
            payment_date=payment_date,
            method=method,
            description=(description or "").strip(),
            reference_number=(reference_number or "").strip(),
            reference=(reference_number or "").strip(),
        )

        for row in allocations:
            receipt_scope = apply_site_scope(
                Receipt.objects.filter(id=row["receipt_id"], supplier_id=supplier_id),
                field_name="warehouse_id",
                assigned_site_ids=assigned_site_ids,
                active_site_id=active_site_id,
            )
            receipt = receipt_scope.first()
            if not receipt:
                raise ValidationException(f"Receipt {row['receipt_id']} does not belong to selected supplier.")
            PaymentAllocation.objects.create(
                payment=payment,
                receipt=receipt,
                amount_allocated=row["amount_allocated"],
            )

        return payment
