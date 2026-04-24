from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.models.event import Event
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.room import Room
from app.models.inventory_item import InventoryItem

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/daily-briefing")
def daily_briefing(db: Session = Depends(get_db)):
    today = date.today()
    next_7 = today + timedelta(days=7)

    checkins_today = db.query(Booking).filter(
        Booking.check_in == today,
        Booking.status == "confirmed",
    ).all()

    checkouts_today = db.query(Booking).filter(
        Booking.check_out == today,
        Booking.status == "checked_in",
    ).all()

    active_events = db.query(Event).filter(
        Event.event_date == today,
        Event.status.notin_(["cancelled"]),
    ).all()

    upcoming_events = db.query(Event).filter(
        Event.event_date > today,
        Event.event_date <= next_7,
        Event.status.notin_(["cancelled"]),
    ).all()

    upcoming_checkins = db.query(Booking).filter(
        Booking.check_in > today,
        Booking.check_in <= next_7,
        Booking.status == "confirmed",
    ).all()

    # Revenue today = payments received today
    revenue_today = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_date == today,
    ).scalar() or 0

    # Low stock alerts
    low_stock = db.query(InventoryItem).filter(
        InventoryItem.available_quantity <= InventoryItem.low_stock_threshold
    ).all()

    # Overdue invoices
    overdue = db.query(Invoice).filter(
        Invoice.due_date < today,
        Invoice.status.in_(["sent", "overdue"]),
    ).all()

    total_rooms = db.query(Room).count()
    occupied_rooms = db.query(Room).filter(Room.status == "occupied").count()

    return {
        "date": str(today),
        "occupancy": {
            "total_rooms": total_rooms,
            "occupied": occupied_rooms,
            "rate_pct": round(occupied_rooms / total_rooms * 100, 1) if total_rooms else 0,
        },
        "today": {
            "checkins": len(checkins_today),
            "checkouts": len(checkouts_today),
            "active_events": len(active_events),
            "revenue": float(revenue_today),
        },
        "next_7_days": {
            "upcoming_checkins": len(upcoming_checkins),
            "upcoming_events": len(upcoming_events),
        },
        "alerts": {
            "low_stock_items": [
                {"name": i.name, "available": i.available_quantity, "unit": i.unit}
                for i in low_stock
            ],
            "overdue_invoices": len(overdue),
        },
    }


@router.get("/revenue")
def revenue_report(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .filter(Payment.payment_date >= from_date, Payment.payment_date <= to_date)
        .all()
    )

    total = sum(float(p.amount) for p in payments)
    by_method: dict = {}
    for p in payments:
        by_method[p.method] = by_method.get(p.method, 0) + float(p.amount)

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "total_revenue": total,
        "by_payment_method": by_method,
        "payment_count": len(payments),
    }


@router.get("/occupancy")
def occupancy_report(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
):
    total_rooms = db.query(Room).count()
    days = (to_date - from_date).days or 1
    total_room_nights = total_rooms * days

    booked_nights = (
        db.query(Booking)
        .filter(
            Booking.status.notin_(["cancelled", "no_show"]),
            Booking.check_in < to_date,
            Booking.check_out > from_date,
        )
        .all()
    )

    occupied_nights = sum(
        (min(b.check_out, to_date) - max(b.check_in, from_date)).days
        for b in booked_nights
    )

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "total_rooms": total_rooms,
        "occupancy_pct": round(occupied_nights / total_room_nights * 100, 1) if total_room_nights else 0,
        "occupied_room_nights": occupied_nights,
    }
