from __future__ import annotations
from datetime import date
from typing import Optional
import uuid

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.room import Room
from app.models.invoice import Invoice
from app.schemas.booking import BookingCreate
from app.services.invoice_service import create_invoice_for_booking


def get_unavailable_room_ids(db: Session, check_in: date, check_out: date) -> list[int]:
    """Return IDs of rooms that have an overlapping confirmed booking."""
    overlapping = (
        db.query(Booking.room_id)
        .filter(
            Booking.status.notin_(["cancelled", "no_show"]),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        .all()
    )
    return [r.room_id for r in overlapping]


def create_booking(db: Session, data: BookingCreate, created_by: Optional[str] = None) -> tuple[Booking, Invoice]:
    """
    Create a booking with a row lock to prevent double bookings.
    Returns (booking, invoice).
    """
    # Lock the room row for this transaction
    room = (
        db.query(Room)
        .filter(Room.id == data.room_id)
        .with_for_update()
        .first()
    )
    if not room:
        raise ValueError("Room not found")
    if room.status == "maintenance":
        raise ValueError(f"Room {room.room_number} is under maintenance")

    # Re-check availability inside the lock
    conflict = (
        db.query(Booking)
        .filter(
            Booking.room_id == data.room_id,
            Booking.status.notin_(["cancelled", "no_show"]),
            Booking.check_in < data.check_out,
            Booking.check_out > data.check_in,
        )
        .first()
    )
    if conflict:
        raise ValueError(
            f"Room {room.room_number} is already booked from {conflict.check_in} to {conflict.check_out}"
        )

    booking = Booking(
        id=uuid.uuid4(),
        guest_id=data.guest_id,
        room_id=data.room_id,
        check_in=data.check_in,
        check_out=data.check_out,
        adults=data.adults,
        children=data.children,
        special_requests=data.special_requests,
        source=data.source,
        status="confirmed",
        created_by=created_by,
    )
    db.add(booking)
    db.flush()  # get booking.id before creating invoice

    invoice = create_invoice_for_booking(db, booking, room)
    db.flush()

    return booking, invoice
