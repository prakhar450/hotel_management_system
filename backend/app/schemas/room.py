from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class RoomOut(BaseModel):
    id: int
    room_number: str
    type: str
    floor: int
    base_rate: float
    status: str
    amenities: dict

    model_config = {"from_attributes": True}


class RoomUpdate(BaseModel):
    status: Optional[str] = None
    amenities: Optional[dict] = None
    base_rate: Optional[float] = None
