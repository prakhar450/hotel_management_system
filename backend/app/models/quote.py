from __future__ import annotations
from typing import Optional

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, event
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    space_id: Mapped[int] = mapped_column(ForeignKey("event_spaces.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    line_items: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # draft/sent/accepted/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    lead = relationship("Lead", lazy="select")
    space = relationship("EventSpace", lazy="select")


@event.listens_for(Quote, "before_update")
def _quote_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
