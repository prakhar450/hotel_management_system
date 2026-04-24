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


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    event_type: Mapped[Optional[str]] = mapped_column(String(50))
    event_date: Mapped[Optional[str]] = mapped_column(String(20))  # flexible — may be approximate
    guest_count: Mapped[Optional[int]] = mapped_column()
    budget_range: Mapped[Optional[str]] = mapped_column(String(100))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    # new/contacted/site_visit/quoted/won/lost
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


@event.listens_for(Lead, "before_update")
def _lead_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
