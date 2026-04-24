from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.booking import BookingCreate, BookingUpdate, BookingOut, BookingWithInvoice
from app.services.booking_service import create_booking

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


@router.post("", response_model=BookingWithInvoice, status_code=201)
def new_booking(data: BookingCreate, db: Session = Depends(get_db)):
    try:
        booking, invoice = create_booking(db, data)
        db.commit()
        db.refresh(booking)
        db.refresh(invoice)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

    return BookingWithInvoice(
        booking=BookingOut.model_validate(booking),
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        invoice_total=float(invoice.total_amount),
    )


@router.get("", response_model=list[BookingOut])
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
    return q.order_by(Booking.check_in).all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


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
