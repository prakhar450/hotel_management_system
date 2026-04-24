from __future__ import annotations
from typing import Optional

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # linen/furniture/av/crockery/decor/other
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


@event.listens_for(InventoryItem, "before_update")
def _item_updated_at(mapper, connection, target):
    target.updated_at = _utcnow()
