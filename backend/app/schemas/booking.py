from __future__ import annotations
from typing import Optional
from datetime import date, datetime
import uuid
from pydantic import BaseModel, model_validator


class BookingCreate(BaseModel):
    guest_id: uuid.UUID
    room_id: int
    check_in: date
    check_out: date
    adults: int = 1
    children: int = 0
    special_requests: Optional[str] = None
    source: str = "walk_in"

    @model_validator(mode="after")
    def check_in_before_check_out(self) -> "BookingCreate":
        if self.check_in >= self.check_out:
            raise ValueError("check_out must be after check_in")
        return self


class BookingUpdate(BaseModel):
    special_requests: Optional[str] = None
    source: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None


class BookingOut(BaseModel):
    id: uuid.UUID
    guest_id: uuid.UUID
    room_id: int
    check_in: date
    check_out: date
    actual_checkin: Optional[datetime]
    actual_checkout: Optional[datetime]
    status: str
    adults: int
    children: int
    special_requests: Optional[str]
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingWithInvoice(BaseModel):
    booking: BookingOut
    invoice_id: Optional[uuid.UUID] = None
    invoice_number: Optional[str] = None
    invoice_total: Optional[float] = None
