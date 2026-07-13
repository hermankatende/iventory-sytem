from dataclasses import dataclass


@dataclass(frozen=True)
class StockAdjustment:
    item_id: int
    warehouse_id: int
    delta: int
    reason: str
