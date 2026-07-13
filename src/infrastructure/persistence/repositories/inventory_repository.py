from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q, Sum

from src.application.common.exceptions.domain_exceptions import NotFoundException
from src.application.common.interfaces.repositories import InventoryRepository
from src.infrastructure.persistence.models import Item, Product, StockLevel, StockMovement, Warehouse


class DjangoInventoryRepository(InventoryRepository):
    def get_stock_level(self, item_id: int, warehouse_id: int) -> int:
        try:
            stock = StockLevel.objects.get(item_id=item_id, warehouse_id=warehouse_id)
            return stock.qty_on_hand
        except StockLevel.DoesNotExist as exc:
            raise NotFoundException("Stock level not found") from exc

    @transaction.atomic
    def adjust_stock(self, item_id: int, warehouse_id: int, delta: int, reason: str) -> None:
        try:
            item = Item.objects.get(pk=item_id)
            warehouse = Warehouse.objects.get(pk=warehouse_id)
        except (Item.DoesNotExist, Warehouse.DoesNotExist) as exc:
            raise NotFoundException("Item or warehouse not found") from exc

        stock, _ = StockLevel.objects.select_for_update().get_or_create(item=item, warehouse=warehouse)
        if stock.qty_on_hand + delta < 0:
            raise ValueError("Insufficient stock for operation")

        stock.qty_on_hand += delta
        stock.save(update_fields=["qty_on_hand", "updated_at"])

        movement_type = "IN" if delta > 0 else "OUT"
        StockMovement.objects.create(
            item=item,
            warehouse=warehouse,
            movement_type=movement_type,
            delta=delta,
            reason=reason,
        )

    @transaction.atomic
    def transfer_stock(self, item_id: int, source_warehouse_id: int, destination_warehouse_id: int, qty: int, reason: str) -> None:
        if qty <= 0:
            raise ValueError("Transfer quantity must be greater than zero")
        if source_warehouse_id == destination_warehouse_id:
            raise ValueError("Source and destination warehouse must be different")

        try:
            item = Item.objects.get(pk=item_id)
            source = Warehouse.objects.get(pk=source_warehouse_id)
            destination = Warehouse.objects.get(pk=destination_warehouse_id)
        except (Item.DoesNotExist, Warehouse.DoesNotExist) as exc:
            raise NotFoundException("Item or warehouse not found") from exc

        first_warehouse, second_warehouse = (
            (source, destination)
            if source.id < destination.id
            else (destination, source)
        )

        first_stock, _ = StockLevel.objects.select_for_update().get_or_create(item=item, warehouse=first_warehouse)
        second_stock, _ = StockLevel.objects.select_for_update().get_or_create(item=item, warehouse=second_warehouse)

        source_stock = first_stock if first_warehouse.id == source.id else second_stock
        destination_stock = first_stock if first_warehouse.id == destination.id else second_stock

        if source_stock.qty_on_hand < qty:
            raise ValueError("Insufficient stock in source warehouse")

        source_stock.qty_on_hand -= qty
        destination_stock.qty_on_hand += qty
        source_stock.save(update_fields=["qty_on_hand", "updated_at"])
        destination_stock.save(update_fields=["qty_on_hand", "updated_at"])

        transfer_ref = f"TR-{item_id}-{source_warehouse_id}-{destination_warehouse_id}"
        StockMovement.objects.create(
            item=item,
            warehouse=source,
            movement_type="TRANSFER",
            delta=-qty,
            reason=reason,
            reference=transfer_ref,
            source_warehouse=source,
            destination_warehouse=destination,
        )
        StockMovement.objects.create(
            item=item,
            warehouse=destination,
            movement_type="TRANSFER",
            delta=qty,
            reason=reason,
            reference=transfer_ref,
            source_warehouse=source,
            destination_warehouse=destination,
        )

    def list_current_stock(self, search: str = "", category_id: int | None = None, warehouse_id: int | None = None) -> list[dict]:
        queryset = StockLevel.objects.select_related("item", "warehouse", "item__product", "item__product__category")

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if search:
            queryset = queryset.filter(
                Q(item__name__icontains=search)
                | Q(item__sku__icontains=search)
                | Q(item__barcode__icontains=search)
                | Q(item__product__product_code__icontains=search)
                | Q(item__product__barcode__icontains=search)
            )
        if category_id:
            queryset = queryset.filter(item__product__category_id=category_id)

        return [
            {
                "item_id": stock.item_id,
                "item_name": stock.item.name,
                "sku": stock.item.sku,
                "product_code": getattr(getattr(stock.item, "product", None), "product_code", ""),
                "warehouse": stock.warehouse.name,
                "warehouse_id": stock.warehouse_id,
                "qty_on_hand": stock.qty_on_hand,
                "unit_cost": float(stock.item.unit_cost),
                "valuation": float(Decimal(stock.qty_on_hand) * stock.item.unit_cost),
                "reorder_level": stock.item.reorder_level,
                "is_low_stock": stock.qty_on_hand <= stock.item.reorder_level,
            }
            for stock in queryset.order_by("item__name", "warehouse__name")
        ]

    def get_inventory_history(self, item_id: int | None = None, warehouse_id: int | None = None) -> list[dict]:
        queryset = StockMovement.objects.select_related("item", "warehouse", "source_warehouse", "destination_warehouse")
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return [
            {
                "id": move.id,
                "item": move.item.name,
                "warehouse": move.warehouse.name,
                "warehouse_id": move.warehouse_id,
                "movement_type": move.movement_type,
                "delta": move.delta,
                "reason": move.reason,
                "reference": move.reference,
                "source_warehouse": move.source_warehouse.name if move.source_warehouse else "",
                "destination_warehouse": move.destination_warehouse.name if move.destination_warehouse else "",
                "created_at": move.created_at,
            }
            for move in queryset.order_by("-created_at")[:1000]
        ]

    def get_stock_valuation(self) -> dict:
        rows = StockLevel.objects.select_related("item", "warehouse")
        total_valuation = Decimal("0")
        per_warehouse = {}

        for row in rows:
            valuation = Decimal(row.qty_on_hand) * row.item.unit_cost
            total_valuation += valuation
            warehouse_name = row.warehouse.name
            per_warehouse[warehouse_name] = per_warehouse.get(warehouse_name, Decimal("0")) + valuation

        return {
            "total_valuation": float(total_valuation),
            "per_warehouse": {name: float(value) for name, value in per_warehouse.items()},
        }

    def get_low_stock_items(self) -> list[dict]:
        queryset = StockLevel.objects.select_related("item", "warehouse").filter(qty_on_hand__lte=F("item__reorder_level"))
        return [
            {
                "item_id": row.item_id,
                "item": row.item.name,
                "warehouse": row.warehouse.name,
                "warehouse_id": row.warehouse_id,
                "qty_on_hand": row.qty_on_hand,
                "reorder_level": row.item.reorder_level,
            }
            for row in queryset.order_by("item__name")
        ]
