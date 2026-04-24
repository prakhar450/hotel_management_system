from __future__ import annotations
from typing import Optional

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    id_type: Mapped[Optional[str]] = mapped_column(String(50))  # aadhaar/passport/dl
    id_number: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    nationality: Mapped[str] = mapped_column(String(100), default="Indian")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


@event.listens_for(Guest, "before_update")
def _guest_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
