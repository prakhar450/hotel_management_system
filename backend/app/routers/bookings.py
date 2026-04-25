from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.models.guest import Guest
from app.models.room import Room
from app.schemas.booking import BookingCreate, BookingUpdate, BookingOut, BookingWithInvoice
from app.services.booking_service import create_booking

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


def _booking_to_dict(b: Booking, guest: Guest | None, room: Room | None) -> dict:
    return {
        "id": str(b.id),
        "guest_id": str(b.guest_id),
        "room_id": b.room_id,
        "check_in": str(b.check_in),
        "check_out": str(b.check_out),
        "actual_checkin": str(b.actual_checkin) if b.actual_checkin else None,
        "actual_checkout": str(b.actual_checkout) if b.actual_checkout else None,
        "status": b.status,
        "adults": b.adults,
        "children": b.children,
        "special_requests": b.special_requests,
        "source": b.source,
        "created_at": str(b.created_at),
        "guest_name": guest.name if guest else "—",
        "room_number": room.room_number if room else "—",
    }


@router.post("", status_code=201)
def new_booking(data: BookingCreate, db: Session = Depends(get_db)):
    try:
        booking, invoice = create_booking(db, data)
        db.commit()
        db.refresh(booking)
        db.refresh(invoice)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

    guest = db.query(Guest).filter(Guest.id == booking.guest_id).first()
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    booking_dict = _booking_to_dict(booking, guest, room)

    return {
        "booking": booking_dict,
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "invoice_total": float(invoice.total_amount),
    }


@router.get("")
def list_bookings(
    status: Optional[str] = Query(None),
    room_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Booking)
    if status:
        q = q.filter(Booking.status == status)
    if room_id:
        q = q.filter(Booking.room_id == room_id)
    if from_date:
        q = q.filter(Booking.check_in >= from_date)
    if to_date:
        q = q.filter(Booking.check_out <= to_date)
    bookings = q.order_by(Booking.check_in).all()
    result = []
    for b in bookings:
        guest = db.query(Guest).filter(Guest.id == b.guest_id).first()
        room = db.query(Room).filter(Room.id == b.room_id).first()
        result.append(_booking_to_dict(b, guest, room))
    return result


@router.get("/{booking_id}")
def get_booking(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    guest = db.query(Guest).filter(Guest.id == booking.guest_id).first()
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    return _booking_to_dict(booking, guest, room)


@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(booking_id: uuid.UUID, data: BookingUpdate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return booking


@router.put("/{booking_id}/checkin", response_model=BookingOut)
def check_in(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail=f"Cannot check in a booking with status '{booking.status}'")

    booking.status = "checked_in"
    booking.actual_checkin = datetime.now(timezone.utc)

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if room:
        room.status = "occupied"

    db.commit()
    db.refresh(booking)
    return booking


@router.put("/{booking_id}/checkout", response_model=BookingOut)
def check_out(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "checked_in":
        raise HTTPException(status_code=400, detail=f"Cannot check out a booking with status '{booking.status}'")

    booking.status = "checked_out"
    booking.actual_checkout = datetime.now(timezone.utc)

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if room:
        room.status = "available"

    db.commit()
    db.refresh(booking)
    return booking


@router.put("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status in ("checked_out", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a booking with status '{booking.status}'")

    booking.status = "cancelled"

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if room and room.status == "occupied":
        room.status = "available"

    db.commit()
    db.refresh(booking)
    return booking


@router.put("/{booking_id}/override", response_model=BookingOut)
def manager_override(
    booking_id: uuid.UUID,
    new_status: str = Query(...),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    return booking
