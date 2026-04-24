from __future__ import annotations
from typing import Optional

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_room_dates", "room_id", "check_in", "check_out"),
        Index("ix_bookings_guest_id", "guest_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    actual_checkin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_checkout: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    # enquiry/confirmed/checked_in/checked_out/cancelled/no_show
    adults: Mapped[int] = mapped_column(Integer, default=1)
    children: Mapped[int] = mapped_column(Integer, default=0)
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="walk_in")
    # walk_in/phone/online/agent
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    guest = relationship("Guest", lazy="select")
    room = relationship("Room", lazy="select")


@event.listens_for(Booking, "before_update")
def _booking_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
