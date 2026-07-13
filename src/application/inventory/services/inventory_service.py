from uuid import uuid4

from src.application.common.exceptions.domain_exceptions import ValidationException
from src.application.common.interfaces.repositories import InventoryRepository
from django.db import transaction
from src.infrastructure.persistence.models import BatchOperation


class InventoryService:
    def __init__(self, inventory_repository: InventoryRepository):
        self.inventory_repository = inventory_repository

    def adjust_stock(self, item_id: int, warehouse_id: int, delta: int, reason: str) -> None:
        if delta == 0:
            raise ValidationException("Delta cannot be zero")
        self.inventory_repository.adjust_stock(item_id=item_id, warehouse_id=warehouse_id, delta=delta, reason=reason)

    def stock_in(self, item_id: int, warehouse_id: int, qty: int, reason: str = "Stock In") -> None:
        if qty <= 0:
            raise ValidationException("Quantity must be greater than zero")
        self.inventory_repository.adjust_stock(item_id=item_id, warehouse_id=warehouse_id, delta=qty, reason=reason)

    def stock_out(self, item_id: int, warehouse_id: int, qty: int, reason: str = "Stock Out") -> None:
        if qty <= 0:
            raise ValidationException("Quantity must be greater than zero")
        self.inventory_repository.adjust_stock(item_id=item_id, warehouse_id=warehouse_id, delta=-qty, reason=reason)

    def transfer_between_sites(self, item_id: int, source_warehouse_id: int, destination_warehouse_id: int, qty: int, reason: str = "Site Transfer") -> None:
        if qty <= 0:
            raise ValidationException("Transfer quantity must be greater than zero")
        self.inventory_repository.transfer_stock(
            item_id=item_id,
            source_warehouse_id=source_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            qty=qty,
            reason=reason,
        )

    def get_stock_level(self, item_id: int, warehouse_id: int) -> int:
        return self.inventory_repository.get_stock_level(item_id=item_id, warehouse_id=warehouse_id)

    def get_current_stock(self, search: str = "", category_id: int | None = None, warehouse_id: int | None = None) -> list[dict]:
        return self.inventory_repository.list_current_stock(search=search, category_id=category_id, warehouse_id=warehouse_id)

    def get_stock_valuation(self) -> dict:
        return self.inventory_repository.get_stock_valuation()

    def get_low_stock_alerts(self) -> list[dict]:
        return self.inventory_repository.get_low_stock_items()

    def get_inventory_history(self, item_id: int | None = None, warehouse_id: int | None = None) -> list[dict]:
        return self.inventory_repository.get_inventory_history(item_id=item_id, warehouse_id=warehouse_id)

    @transaction.atomic
    def process_batch_adjustments(self, operation_type: str, operations: list[dict], reason: str = "Batch Operation") -> str:
        if not operations:
            raise ValidationException("No operations provided for batch processing")

        batch = BatchOperation.objects.create(
            batch_id=f"BATCH-{uuid4().hex[:12].upper()}",
            operation_type=operation_type,
            total_lines=len(operations),
            processed_lines=0,
            status="RUNNING",
        )

        try:
            for operation in operations:
                if operation_type == "STOCK_IN":
                    self.stock_in(operation["item_id"], operation["warehouse_id"], operation["qty"], reason)
                elif operation_type == "STOCK_OUT":
                    self.stock_out(operation["item_id"], operation["warehouse_id"], operation["qty"], reason)
                elif operation_type == "ADJUST":
                    self.adjust_stock(operation["item_id"], operation["warehouse_id"], operation["delta"], reason)
                elif operation_type == "TRANSFER":
                    self.transfer_between_sites(
                        operation["item_id"],
                        operation["source_warehouse_id"],
                        operation["destination_warehouse_id"],
                        operation["qty"],
                        reason,
                    )
                else:
                    raise ValidationException("Unsupported batch operation type")

                batch.processed_lines += 1
                batch.save(update_fields=["processed_lines"])
        except Exception:
            batch.status = "FAILED"
            batch.save(update_fields=["status"])
            raise

        batch.status = "COMPLETED"
        batch.save(update_fields=["status"])
        return batch.batch_id

    def get_stock_reports(self) -> dict:
        current_stock = self.get_current_stock()
        low_stock = self.get_low_stock_alerts()
        valuation = self.get_stock_valuation()

        return {
            "summary": {
                "total_products": len({entry["item_id"] for entry in current_stock}),
                "total_stock_rows": len(current_stock),
                "low_stock_count": len(low_stock),
                "total_valuation": valuation["total_valuation"],
            },
            "low_stock": low_stock,
            "valuation": valuation,
            "current_stock": current_stock,
        }

    def get_dashboard_cards(self) -> dict:
        reports = self.get_stock_reports()
        movement_history = self.get_inventory_history()[:100]

        stock_in_count = sum(1 for row in movement_history if row["movement_type"] == "IN")
        stock_out_count = sum(1 for row in movement_history if row["movement_type"] == "OUT")
        transfer_count = sum(1 for row in movement_history if row["movement_type"] == "TRANSFER")

        return {
            "total_products": reports["summary"]["total_products"],
            "total_valuation": reports["summary"]["total_valuation"],
            "low_stock_count": reports["summary"]["low_stock_count"],
            "stock_in_count": stock_in_count,
            "stock_out_count": stock_out_count,
            "transfer_count": transfer_count,
        }

    def get_chart_data(self) -> dict:
        valuation = self.get_stock_valuation()
        per_warehouse = valuation["per_warehouse"]

        return {
            "valuation_by_site": {
                "labels": list(per_warehouse.keys()),
                "values": list(per_warehouse.values()),
            }
        }
