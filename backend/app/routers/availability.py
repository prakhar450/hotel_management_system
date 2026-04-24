from __future__ import annotations
from datetime import date, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room import Room
from app.models.event_space import EventSpace
from app.models.booking import Booking
from app.models.event import Event
from app.schemas.room import RoomOut
from app.services.booking_service import get_unavailable_room_ids

router = APIRouter(prefix="/api/v1/availability", tags=["Availability"])


@router.get("/rooms", response_model=list[RoomOut])
def available_rooms(
    check_in: date = Query(...),
    check_out: date = Query(...),
    room_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if check_in >= check_out:
        return []

    unavailable_ids = get_unavailable_room_ids(db, check_in, check_out)

    q = db.query(Room).filter(
        Room.status.notin_(["maintenance", "blocked"]),
        Room.id.notin_(unavailable_ids),
    )
    if room_type:
        q = q.filter(Room.type == room_type)

    return q.order_by(Room.room_number).all()


@router.get("/spaces")
def available_spaces(
    event_date: date = Query(...),
    start_time: time = Query(...),
    end_time: time = Query(...),
    db: Session = Depends(get_db),
):
    """Return spaces with no overlapping event (including setup/teardown buffers)."""
    all_spaces = db.query(EventSpace).filter(EventSpace.status == "available").all()

    result = []
    for space in all_spaces:
        conflict = (
            db.query(Event)
            .filter(
                Event.space_id == space.id,
                Event.event_date == event_date,
                Event.status.notin_(["cancelled"]),
                Event.start_time < end_time,
                Event.end_time > start_time,
            )
            .first()
        )
        if not conflict:
            result.append({
                "id": space.id,
                "name": space.name,
                "type": space.type,
                "capacity": space.capacity,
                "base_rate_per_day": float(space.base_rate_per_day),
                "base_rate_per_slot": float(space.base_rate_per_slot),
                "amenities": space.amenities,
            })

    return result


@router.get("/calendar")
def calendar_view(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
):
    """All bookings and events for a given month."""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)

    bookings = (
        db.query(Booking)
        .filter(Booking.check_in <= end, Booking.check_out >= start)
        .filter(Booking.status.notin_(["cancelled", "no_show"]))
        .all()
    )
    events = (
        db.query(Event)
        .filter(Event.event_date >= start, Event.event_date <= end)
        .filter(Event.status.notin_(["cancelled"]))
        .all()
    )

    return {
        "bookings": [
            {
                "id": str(b.id), "room_id": b.room_id,
                "check_in": str(b.check_in), "check_out": str(b.check_out),
                "status": b.status, "guest_id": str(b.guest_id),
            }
            for b in bookings
        ],
        "events": [
            {
                "id": str(e.id), "name": e.name, "space_id": e.space_id,
                "event_date": str(e.event_date), "event_type": e.event_type,
                "status": e.status,
            }
            for e in events
        ],
    }
