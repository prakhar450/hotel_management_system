from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from sqlalchemy import DateTime, Numeric, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # single/double/suite/deluxe
    floor: Mapped[int] = mapped_column(nullable=False)
    base_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="available")  # available/occupied/maintenance/blocked
    amenities: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


@event.listens_for(Room, "before_update")
def _room_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
