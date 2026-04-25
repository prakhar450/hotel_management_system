from __future__ import annotations
from typing import Optional
from datetime import date, datetime, time
import uuid
from pydantic import BaseModel


class EventCreate(BaseModel):
    name: Optional[str] = None
    event_type: str
    guest_id: Optional[uuid.UUID] = None
    space_id: int
    event_date: date
    start_time: time
    end_time: time
    guest_count: int
    special_requirements: Optional[str] = None


class EventUpdate(BaseModel):
    name: Optional[str] = None
    guest_count: Optional[int] = None
    special_requirements: Optional[str] = None
    status: Optional[str] = None


class EventOut(BaseModel):
    id: uuid.UUID
    name: str
    event_type: str
    guest_id: Optional[uuid.UUID]
    space_id: int
    event_date: date
    start_time: time
    end_time: time
    guest_count: int
    status: str
    special_requirements: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
