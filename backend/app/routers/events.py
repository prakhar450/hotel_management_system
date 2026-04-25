from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.event_space import EventSpace
from app.schemas.event import EventCreate, EventUpdate, EventOut
from app.services.invoice_service import create_invoice_for_event

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get("/spaces")
def list_spaces(db: Session = Depends(get_db)):
    spaces = db.query(EventSpace).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "capacity": s.capacity,
            "base_rate_per_day": float(s.base_rate_per_day),
        }
        for s in spaces
    ]


@router.post("", status_code=201)
def create_event(data: EventCreate, db: Session = Depends(get_db)):
    space = db.query(EventSpace).filter(EventSpace.id == data.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Event space not found")

    # Check for time overlap
    conflict = (
        db.query(Event)
        .filter(
            Event.space_id == data.space_id,
            Event.event_date == data.event_date,
            Event.status.notin_(["cancelled"]),
            Event.start_time < data.end_time,
            Event.end_time > data.start_time,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"{space.name} is already booked on {data.event_date} from {conflict.start_time} to {conflict.end_time}"
        )

    event_name = data.name or f"{data.event_type.title()} Event"
    event_data = data.model_dump()
    event_data["name"] = event_name
    # Only include guest_id if provided
    if event_data.get("guest_id") is None:
        event_data.pop("guest_id", None)

    event = Event(id=uuid.uuid4(), **event_data)
    db.add(event)
    db.flush()

    invoice = create_invoice_for_event(db, event, space)
    db.commit()
    db.refresh(event)
    db.refresh(invoice)

    return {
        "event": EventOut.model_validate(event),
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "invoice_total": float(invoice.total_amount),
    }


@router.get("")
def list_events(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if from_date:
        q = q.filter(Event.event_date >= from_date)
    if to_date:
        q = q.filter(Event.event_date <= to_date)
    if status:
        q = q.filter(Event.status == status)
    events = q.order_by(Event.event_date).all()
    result = []
    for e in events:
        space = db.query(EventSpace).filter(EventSpace.id == e.space_id).first()
        result.append({
            "id": str(e.id),
            "name": e.name,
            "event_type": e.event_type,
            "space_id": e.space_id,
            "space_name": space.name if space else "—",
            "event_date": str(e.event_date),
            "start_time": str(e.start_time),
            "end_time": str(e.end_time),
            "guest_count": e.guest_count,
            "status": e.status,
            "special_requirements": e.special_requirements,
            "created_at": str(e.created_at),
        })
    return result


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: uuid.UUID, data: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.put("/{event_id}/cancel", response_model=EventOut)
def cancel_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status == "cancelled":
        raise HTTPException(status_code=400, detail="Event is already cancelled")
    event.status = "cancelled"
    db.commit()
    db.refresh(event)
    return event
