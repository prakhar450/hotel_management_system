from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventSpace(Base):
    __tablename__ = "event_spaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # hall/lawn/terrace
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    base_rate_per_day: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    base_rate_per_slot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    setup_time_hours: Mapped[float] = mapped_column(Numeric(4, 1), default=2.0)
    teardown_time_hours: Mapped[float] = mapped_column(Numeric(4, 1), default=2.0)
    amenities: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


@event.listens_for(EventSpace, "before_update")
def _space_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
