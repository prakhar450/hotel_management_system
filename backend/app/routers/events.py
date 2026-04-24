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

    event = Event(id=uuid.uuid4(), **data.model_dump())
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


@router.get("", response_model=list[EventOut])
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
    return q.order_by(Event.event_date).all()


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
