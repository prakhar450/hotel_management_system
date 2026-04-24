from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.guest import Guest
from app.models.booking import Booking
from app.models.event import Event
from app.schemas.guest import GuestCreate, GuestUpdate, GuestOut

router = APIRouter(prefix="/api/v1/guests", tags=["Guests"])


@router.post("", response_model=GuestOut, status_code=201)
def create_guest(data: GuestCreate, db: Session = Depends(get_db)):
    existing = db.query(Guest).filter(Guest.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Guest with phone {data.phone} already exists")

    guest = Guest(id=uuid.uuid4(), **data.model_dump())
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


@router.get("", response_model=list[GuestOut])
def search_guests(
    q: Optional[str] = Query(None, description="Search by name or phone"),
    db: Session = Depends(get_db),
):
    query = db.query(Guest)
    if q:
        query = query.filter(
            Guest.name.ilike(f"%{q}%") | Guest.phone.ilike(f"%{q}%")
        )
    return query.order_by(Guest.name).limit(50).all()


@router.get("/{guest_id}", response_model=GuestOut)
def get_guest(guest_id: uuid.UUID, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.put("/{guest_id}", response_model=GuestOut)
def update_guest(guest_id: uuid.UUID, data: GuestUpdate, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(guest, field, value)
    db.commit()
    db.refresh(guest)
    return guest


@router.get("/{guest_id}/history")
def guest_history(guest_id: uuid.UUID, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    bookings = db.query(Booking).filter(Booking.guest_id == guest_id).order_by(Booking.check_in.desc()).all()
    events = db.query(Event).filter(Event.guest_id == guest_id).order_by(Event.event_date.desc()).all()

    return {
        "guest": GuestOut.model_validate(guest),
        "bookings": [
            {"id": str(b.id), "room_id": b.room_id, "check_in": str(b.check_in),
             "check_out": str(b.check_out), "status": b.status}
            for b in bookings
        ],
        "events": [
            {"id": str(e.id), "name": e.name, "event_date": str(e.event_date), "status": e.status}
            for e in events
        ],
    }
