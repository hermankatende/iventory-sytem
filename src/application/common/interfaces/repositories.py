from abc import ABC, abstractmethod
from typing import Any


class InventoryRepository(ABC):
    @abstractmethod
    def get_stock_level(self, item_id: int, warehouse_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def adjust_stock(self, item_id: int, warehouse_id: int, delta: int, reason: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def transfer_stock(self, item_id: int, source_warehouse_id: int, destination_warehouse_id: int, qty: int, reason: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_current_stock(self, search: str = "", category_id: int | None = None, warehouse_id: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_inventory_history(self, item_id: int | None = None, warehouse_id: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_stock_valuation(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_low_stock_items(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class SupplierRepository(ABC):
    @abstractmethod
    def list_active_suppliers(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class AuditRepository(ABC):
    @abstractmethod
    def save(self, actor: str, action: str, metadata: dict[str, Any]) -> None:
        raise NotImplementedError


class NotificationRepository(ABC):
    @abstractmethod
    def enqueue(self, channel: str, recipient: str, message: str) -> None:
        raise NotImplementedError
