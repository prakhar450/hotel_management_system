from __future__ import annotations
from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, field_validator


class GuestCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    nationality: str = "Indian"
    notes: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def phone_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Phone number is required")
        return v


class GuestUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    nationality: Optional[str] = None
    notes: Optional[str] = None


class GuestOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: Optional[str]
    id_type: Optional[str]
    id_number: Optional[str]
    address: Optional[str]
    nationality: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
