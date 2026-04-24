from __future__ import annotations
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel


class LeadCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    guest_count: Optional[int] = None
    budget_range: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    event_date: Optional[str] = None
    guest_count: Optional[int] = None
    budget_range: Optional[str] = None


class LeadOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: Optional[str]
    event_type: Optional[str]
    event_date: Optional[str]
    guest_count: Optional[int]
    budget_range: Optional[str]
    source: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    last_contacted_at: Optional[datetime]

    model_config = {"from_attributes": True}
