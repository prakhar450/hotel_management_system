from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class InventoryItemOut(BaseModel):
    id: int
    name: str
    category: str
    total_quantity: int
    available_quantity: int
    low_stock_threshold: int
    unit: str
    notes: Optional[str]
    is_low_stock: bool = False

    model_config = {"from_attributes": True}


class ReserveRequest(BaseModel):
    event_id: str
    item_id: int
    quantity: int


class ReleaseRequest(BaseModel):
    event_id: str
    item_id: int
    quantity: int


class InventoryAlert(BaseModel):
    type: str        # low_stock | maintenance | conflict
    message: str
    severity: str    # warning | critical
