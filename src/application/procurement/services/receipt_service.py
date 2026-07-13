"""Receipt domain service.

Handles receipt lifecycle, edit audit logs, and stock posting when receipts are recorded.
"""

from decimal import Decimal
import json

from django.db import transaction
from django.forms.models import model_to_dict
from django.utils import timezone

from src.application.common.exceptions.domain_exceptions import NotFoundException, ValidationException
from src.application.inventory.services.inventory_service import InventoryService
from src.infrastructure.persistence.models import AuditLog, Item, Product, ProductPrice, Receipt, ReceiptEditLog, ReceiptLine, Supplier, Warehouse
from src.infrastructure.persistence.repositories.inventory_repository import DjangoInventoryRepository
from src.shared.utils.app_logger import get_app_logger
from src.shared.utils.site_context import apply_site_scope
from src.shared.validators.receipt_validation import ReceiptValidator


logger = get_app_logger("app.receipts")


class ReceiptService:
    """Application service for receipt management use cases."""

    def __init__(self):
        self.inventory_service = InventoryService(DjangoInventoryRepository())

    def _validate_reason(self, reason: str) -> None:
        ReceiptValidator.validate_reason(reason)

    def _serialize_receipt_state(self, receipt: Receipt) -> dict:
        lines = list(
            receipt.lines.select_related("item", "product")
            .values("id", "item_id", "product_id", "quantity", "unit_price", "line_total", "total")
            .order_by("id")
        )
        return {
            "receipt": model_to_dict(
                receipt,
                fields=[
                    "id",
                    "receipt_number",
                    "supplier",
                    "warehouse",
                    "source_type",
                    "receipt_date",
                    "notes",
                    "reason_for_edit",
                    "total_amount",
                    "is_recorded",
                ],
            ),
            "lines": lines,
        }

    def _record_audit_snapshot(self, *, receipt: Receipt, user, reason: str, action_type: str, previous_state: dict) -> None:
        AuditLog.objects.create(
            user=user,
            table_name="Receipt",
            record_id=str(receipt.id),
            action_type=action_type,
            reason=reason.strip(),
            date_time=timezone.now(),
            event_metadata={"previous_state": previous_state},
            actor=getattr(user, "username", "system"),
            action=f"{action_type} receipt:{receipt.id}",
            metadata={"reason": reason.strip()},
        )

    def _current_product_price(self, *, product: Product, receipt_date) -> Decimal:
        price_row = (
            ProductPrice.objects.filter(product=product, effective_date__lte=receipt_date)
            .order_by("-effective_date")
            .first()
        )
        if not price_row:
            raise ValidationException(f"No ProductPrice found for product {product.product_code} on {receipt_date}.")
        return price_row.price

    def _recalculate_receipt_total(self, receipt: Receipt) -> None:
        total_amount = Decimal("0")
        for line in receipt.lines.all():
            total_amount += line.total
        receipt.total_amount = total_amount
        receipt.save(update_fields=["total_amount", "updated_at"])

    def _log_change(self, *, receipt: Receipt, field_name: str, old_value, new_value, reason: str, editor, line=None) -> None:
        ReceiptEditLog.objects.create(
            receipt=receipt,
            line=line,
            field_name=field_name,
            old_value=str(old_value if old_value is not None else ""),
            new_value=str(new_value if new_value is not None else ""),
            reason=reason.strip(),
            editor=editor,
            edit_date=timezone.localdate(),
        )

    def _get_item(self, item_id: int) -> Item:
        item = Item.objects.filter(id=item_id).first()
        if not item:
            raise NotFoundException("Item not found.")
        return item

    def _apply_receipt_stock(self, receipt: Receipt) -> None:
        """Post stock-in rows for each receipt line."""
        for line in receipt.lines.select_related("item").all():
            self.inventory_service.stock_in(
                item_id=line.item_id,
                warehouse_id=receipt.warehouse_id,
                qty=line.quantity,
                reason=f"Receipt {receipt.receipt_number}",
            )
        logger.info("receipt.stock_posted receipt=%s lines=%s", receipt.receipt_number, receipt.lines.count())

    @transaction.atomic
    def create_receipt(
        self,
        *,
        receipt_number: str,
        supplier_id: int,
        warehouse_id: int,
        source_type: str,
        receipt_date,
        notes: str,
        scan_file,
        lines: list[dict],
        created_by,
    ) -> Receipt:
        """Create a receipt with lines and optionally auto-record company-origin receipts."""
        receipt_number = (receipt_number or "").strip()
        ReceiptValidator.validate_header(receipt_number=receipt_number, source_type=source_type)
        if Receipt.objects.filter(receipt_number=receipt_number).exists():
            raise ValidationException("Receipt number already exists and must remain unique.")
        if not lines:
            raise ValidationException("A receipt must contain at least one product line.")

        supplier = Supplier.objects.filter(id=supplier_id).first()
        warehouse = Warehouse.objects.filter(id=warehouse_id).first()
        if not supplier or not warehouse:
            raise ValidationException("Supplier and warehouse are required.")

        receipt = Receipt.objects.create(
            receipt_number=receipt_number,
            supplier=supplier,
            warehouse=warehouse,
            source_type=source_type,
            receipt_date=receipt_date,
            notes=notes or "",
            scan_file=scan_file,
            created_by=created_by,
            entered_by=created_by,
            is_recorded=(source_type == "COMPANY"),
            recorded_by=created_by if source_type == "COMPANY" else None,
            recorded_at=timezone.now() if source_type == "COMPANY" else None,
        )

        for payload in lines:
            quantity = int(payload["quantity"])

            product_id = payload.get("product_id")
            if product_id:
                product = Product.objects.select_related("item").filter(id=int(product_id)).first()
                if not product:
                    raise ValidationException("Product not found.")
                item = product.item
                unit_price_decimal = self._current_product_price(product=product, receipt_date=receipt_date)
            else:
                item = self._get_item(int(payload["item_id"]))
                product = Product.objects.filter(item=item).first()
                if product:
                    unit_price_decimal = self._current_product_price(product=product, receipt_date=receipt_date)
                else:
                    unit_price_decimal = Decimal(str(payload.get("unit_price", 0)))

            ReceiptValidator.validate_line(quantity=quantity, unit_price=float(unit_price_decimal))
            ReceiptLine.objects.create(
                receipt=receipt,
                item=item,
                product=product,
                quantity=quantity,
                unit_price=unit_price_decimal,
            )

        self._recalculate_receipt_total(receipt)

        if receipt.is_recorded:
            self._apply_receipt_stock(receipt)

        logger.info(
            "receipt.created number=%s source=%s supplier_id=%s warehouse_id=%s lines=%s",
            receipt.receipt_number,
            receipt.source_type,
            supplier_id,
            warehouse_id,
            len(lines),
        )

        return receipt

    @transaction.atomic
    def edit_receipt_header(self, *, receipt_id: int, editor, reason: str, updates: dict) -> Receipt:
        """Edit mutable receipt header fields and create audit entries per field change."""
        self._validate_reason(reason)
        receipt = Receipt.objects.select_for_update().filter(id=receipt_id).first()
        if not receipt:
            raise NotFoundException("Receipt not found.")

        previous_state = self._serialize_receipt_state(receipt)

        disallowed = {"receipt_number"}
        for key in disallowed:
            updates.pop(key, None)

        tracked_fields = ["supplier_id", "warehouse_id", "source_type", "receipt_date", "notes", "scan_file"]
        dirty_fields = []
        for field in tracked_fields:
            if field in updates and updates[field] is not None:
                old_value = getattr(receipt, field)
                new_value = updates[field]
                if old_value != new_value:
                    setattr(receipt, field, new_value)
                    dirty_fields.append(field)
                    self._log_change(
                        receipt=receipt,
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        reason=reason,
                        editor=editor,
                    )

        if dirty_fields:
            receipt.edited_by = editor
            receipt.reason_for_edit = reason.strip()
            if "edited_by" not in dirty_fields:
                dirty_fields.append("edited_by")
            if "reason_for_edit" not in dirty_fields:
                dirty_fields.append("reason_for_edit")
            receipt.save(update_fields=dirty_fields + ["updated_at"])
            self._record_audit_snapshot(
                receipt=receipt,
                user=editor,
                reason=reason,
                action_type="UPDATE",
                previous_state=previous_state,
            )
            logger.info("receipt.header_updated receipt=%s editor=%s fields=%s", receipt.receipt_number, getattr(editor, "username", "system"), ",".join(dirty_fields))
        return receipt

    @transaction.atomic
    def upsert_line(
        self,
        *,
        receipt_id: int,
        editor,
        reason: str,
        line_id: int | None,
        item_id: int,
        quantity: int,
        unit_price: float,
    ) -> ReceiptLine:
        """Insert or update a receipt line with mandatory reason-based change logs."""
        self._validate_reason(reason)
        ReceiptValidator.validate_line(quantity=quantity, unit_price=unit_price)

        receipt = Receipt.objects.select_for_update().filter(id=receipt_id).first()
        if not receipt:
            raise NotFoundException("Receipt not found.")

        previous_state = self._serialize_receipt_state(receipt)

        item = self._get_item(item_id)
        product = Product.objects.filter(item=item).first()

        unit_price_decimal = Decimal(str(unit_price))
        if product:
            unit_price_decimal = self._current_product_price(product=product, receipt_date=receipt.receipt_date)
        if line_id:
            line = ReceiptLine.objects.select_for_update().filter(id=line_id, receipt=receipt).first()
            if not line:
                raise NotFoundException("Receipt line not found.")

            if line.item_id != item.id:
                self._log_change(
                    receipt=receipt,
                    line=line,
                    field_name="item_id",
                    old_value=line.item_id,
                    new_value=item.id,
                    reason=reason,
                    editor=editor,
                )
                line.item = item

            if line.quantity != quantity:
                self._log_change(
                    receipt=receipt,
                    line=line,
                    field_name="quantity",
                    old_value=line.quantity,
                    new_value=quantity,
                    reason=reason,
                    editor=editor,
                )
                line.quantity = quantity

            if float(line.unit_price) != float(unit_price_decimal):
                self._log_change(
                    receipt=receipt,
                    line=line,
                    field_name="unit_price",
                    old_value=line.unit_price,
                    new_value=unit_price_decimal,
                    reason=reason,
                    editor=editor,
                )
                line.unit_price = unit_price_decimal

            if line.product_id != (product.id if product else None):
                self._log_change(
                    receipt=receipt,
                    line=line,
                    field_name="product_id",
                    old_value=line.product_id,
                    new_value=product.id if product else None,
                    reason=reason,
                    editor=editor,
                )
                line.product = product

            line.save()
            receipt.edited_by = editor
            receipt.reason_for_edit = reason.strip()
            receipt.save(update_fields=["edited_by", "reason_for_edit", "updated_at"])
            self._recalculate_receipt_total(receipt)
            self._record_audit_snapshot(
                receipt=receipt,
                user=editor,
                reason=reason,
                action_type="UPDATE",
                previous_state=previous_state,
            )
            logger.info("receipt.line_updated receipt=%s line_id=%s editor=%s", receipt.receipt_number, line.id, getattr(editor, "username", "system"))
            return line

        existing = ReceiptLine.objects.filter(receipt=receipt, item=item).first()
        if existing:
            raise ValidationException("Item already exists on this receipt. Edit the existing line instead.")

        line = ReceiptLine.objects.create(
            receipt=receipt,
            item=item,
            product=product,
            quantity=quantity,
            unit_price=unit_price_decimal,
        )
        self._log_change(
            receipt=receipt,
            line=line,
            field_name="line_created",
            old_value="",
            new_value=f"item={item.id},qty={quantity},unit_price={unit_price}",
            reason=reason,
            editor=editor,
        )
        receipt.edited_by = editor
        receipt.reason_for_edit = reason.strip()
        receipt.save(update_fields=["edited_by", "reason_for_edit", "updated_at"])
        self._recalculate_receipt_total(receipt)
        self._record_audit_snapshot(
            receipt=receipt,
            user=editor,
            reason=reason,
            action_type="UPDATE",
            previous_state=previous_state,
        )
        logger.info("receipt.line_created receipt=%s line_id=%s editor=%s", receipt.receipt_number, line.id, getattr(editor, "username", "system"))
        return line

    @transaction.atomic
    def record_receipt(self, *, receipt_id: int, editor, reason: str) -> Receipt:
        """Mark receipt as recorded and post inventory stock in one atomic transaction."""
        self._validate_reason(reason)
        receipt = Receipt.objects.select_for_update().filter(id=receipt_id).first()
        if not receipt:
            raise NotFoundException("Receipt not found.")
        if receipt.is_recorded:
            return receipt
        if not receipt.lines.exists():
            raise ValidationException("Receipt must contain at least one line before recording.")

        receipt.is_recorded = True
        receipt.recorded_by = editor
        receipt.recorded_at = timezone.now()
        receipt.save(update_fields=["is_recorded", "recorded_by", "recorded_at", "updated_at"])
        self._apply_receipt_stock(receipt)

        self._log_change(
            receipt=receipt,
            field_name="is_recorded",
            old_value=False,
            new_value=True,
            reason=reason,
            editor=editor,
        )
        logger.info("receipt.recorded receipt=%s editor=%s", receipt.receipt_number, getattr(editor, "username", "system"))
        return receipt

    def list_receipts(self, search: str = "", *, assigned_site_ids=None, active_site_id=None) -> list[Receipt]:
        queryset = apply_site_scope(
            Receipt.objects.select_related("supplier", "warehouse", "created_by", "recorded_by"),
            field_name="warehouse_id",
            assigned_site_ids=assigned_site_ids,
            active_site_id=active_site_id,
        )
        if search:
            queryset = queryset.filter(receipt_number__icontains=search)
        return list(queryset.order_by("-created_at")[:500])

    def get_receipt(self, receipt_id: int) -> Receipt:
        receipt = Receipt.objects.select_related("supplier", "warehouse").prefetch_related("lines__item", "edit_logs__editor").filter(id=receipt_id).first()
        if not receipt:
            raise NotFoundException("Receipt not found.")
        return receipt

    def parse_lines_json(self, lines_json: str) -> list[dict]:
        """Validate and normalize JSON payload for receipt lines."""
        try:
            rows = json.loads(lines_json or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationException("Invalid product lines JSON.") from exc

        if not isinstance(rows, list) or not rows:
            raise ValidationException("Product lines must be a non-empty JSON list.")

        normalized: list[dict] = []
        for idx, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValidationException(f"Line {idx}: invalid object.")
            if "quantity" not in row:
                raise ValidationException(f"Line {idx}: quantity is required.")

            if "product_id" not in row and "item_id" not in row:
                raise ValidationException(f"Line {idx}: product_id or item_id is required.")

            payload = {
                "quantity": int(row["quantity"]),
            }
            if "product_id" in row and row["product_id"] is not None:
                payload["product_id"] = int(row["product_id"])
            if "item_id" in row and row["item_id"] is not None:
                payload["item_id"] = int(row["item_id"])
            if "unit_price" in row and row["unit_price"] is not None:
                payload["unit_price"] = float(row["unit_price"])

            normalized.append(payload)
        return normalized
