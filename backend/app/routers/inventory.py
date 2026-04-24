from __future__ import annotations
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room import Room
from app.models.inventory_item import InventoryItem
from app.models.inventory_usage import InventoryUsage
from app.models.event import Event
from app.schemas.inventory import InventoryItemOut, ReserveRequest, ReleaseRequest, InventoryAlert

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


@router.get("/rooms")
def room_status(db: Session = Depends(get_db)):
    rooms = db.query(Room).order_by(Room.room_number).all()
    return [
        {
            "id": r.id, "room_number": r.room_number, "type": r.type,
            "floor": r.floor, "status": r.status, "base_rate": float(r.base_rate),
            "amenities": r.amenities,
        }
        for r in rooms
    ]


@router.get("/consumables", response_model=list[InventoryItemOut])
def consumable_stock(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.category, InventoryItem.name).all()
    result = []
    for item in items:
        out = InventoryItemOut.model_validate(item)
        out.is_low_stock = item.available_quantity <= item.low_stock_threshold
        result.append(out)
    return result


@router.post("/reserve", status_code=200)
def reserve_items(data: ReserveRequest, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == data.item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.available_quantity < data.quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Only {item.available_quantity} {item.unit} of '{item.name}' available, requested {data.quantity}"
        )

    item.available_quantity -= data.quantity
    usage = InventoryUsage(
        event_id=data.event_id,
        item_id=data.item_id,
        quantity_used=data.quantity,
    )
    db.add(usage)
    db.commit()
    return {"message": f"Reserved {data.quantity} {item.unit} of '{item.name}'", "remaining": item.available_quantity}


@router.post("/release", status_code=200)
def release_items(data: ReleaseRequest, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == data.item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.available_quantity = min(item.total_quantity, item.available_quantity + data.quantity)
    db.commit()
    return {"message": f"Released {data.quantity} {item.unit} of '{item.name}'", "available": item.available_quantity}


@router.get("/alerts", response_model=list[InventoryAlert])
def inventory_alerts(db: Session = Depends(get_db)):
    alerts = []

    # Rooms in maintenance
    maintenance_rooms = db.query(Room).filter(Room.status == "maintenance").all()
    for r in maintenance_rooms:
        alerts.append(InventoryAlert(
            type="maintenance",
            message=f"Room {r.room_number} ({r.type}) is under maintenance",
            severity="warning",
        ))

    # Low stock items
    items = db.query(InventoryItem).all()
    for item in items:
        if item.available_quantity <= item.low_stock_threshold:
            severity = "critical" if item.available_quantity == 0 else "warning"
            alerts.append(InventoryAlert(
                type="low_stock",
                message=f"{item.name}: only {item.available_quantity} {item.unit} left (threshold: {item.low_stock_threshold})",
                severity=severity,
            ))

    # Upcoming events in next 7 days
    today = date.today()
    upcoming = (
        db.query(Event)
        .filter(Event.event_date >= today, Event.event_date <= today + timedelta(days=7))
        .filter(Event.status.notin_(["cancelled"]))
        .all()
    )
    for event in upcoming:
        alerts.append(InventoryAlert(
            type="upcoming_event",
            message=f"{event.name} on {event.event_date} — {event.guest_count} guests",
            severity="warning",
        ))

    return alerts
