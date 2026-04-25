from __future__ import annotations
from typing import Optional, Any
from datetime import date, datetime
import uuid
from pydantic import BaseModel


class InvoiceCreate(BaseModel):
    booking_id: Optional[uuid.UUID] = None
    event_id: Optional[uuid.UUID] = None


class InvoiceOut(BaseModel):
    id: uuid.UUID
    invoice_number: str
    booking_id: Optional[uuid.UUID]
    event_id: Optional[uuid.UUID]
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    status: str
    due_date: date
    line_items: list
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount: float
    method: str
    reference_number: Optional[str] = None
    payment_date: date = None
    notes: Optional[str] = None

    def model_post_init(self, __context):
        if self.payment_date is None:
            object.__setattr__(self, "payment_date", date.today())


class PaymentOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: float
    method: str
    reference_number: Optional[str]
    payment_date: date
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
