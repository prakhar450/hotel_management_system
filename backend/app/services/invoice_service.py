from __future__ import annotations
from datetime import date, timedelta
import uuid

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.event import Event
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.room import Room
from app.models.event_space import EventSpace
from app.utils.invoice_number import next_invoice_number

GST_RATE = 0.18
DEFAULT_DUE_DAYS = 7


def create_invoice_for_booking(db: Session, booking: Booking, room: Room) -> Invoice:
    nights = (booking.check_out - booking.check_in).days
    subtotal = float(room.base_rate) * nights
    tax = round(subtotal * GST_RATE, 2)
    total = round(subtotal + tax, 2)

    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_number=next_invoice_number(db),
        booking_id=booking.id,
        subtotal=subtotal,
        tax_amount=tax,
        discount_amount=0,
        total_amount=total,
        status="sent",
        due_date=booking.check_out + timedelta(days=DEFAULT_DUE_DAYS),
        line_items=[
            {"description": f"Room {room.room_number} — {nights} night(s)", "amount": subtotal},
            {"description": f"GST ({int(GST_RATE * 100)}%)", "amount": tax},
        ],
    )
    db.add(invoice)
    return invoice


def create_invoice_for_event(db: Session, event: Event, space: EventSpace) -> Invoice:
    subtotal = float(space.base_rate_per_day)
    tax = round(subtotal * GST_RATE, 2)
    total = round(subtotal + tax, 2)

    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_number=next_invoice_number(db),
        event_id=event.id,
        subtotal=subtotal,
        tax_amount=tax,
        discount_amount=0,
        total_amount=total,
        status="sent",
        due_date=event.event_date + timedelta(days=DEFAULT_DUE_DAYS),
        line_items=[
            {"description": f"{space.name} — {event.event_type} ({event.name})", "amount": subtotal},
            {"description": f"GST ({int(GST_RATE * 100)}%)", "amount": tax},
        ],
    )
    db.add(invoice)
    return invoice


def update_invoice_status_on_payment(db: Session, invoice: Invoice) -> None:
    """Mark invoice paid when payments cover the full amount, overdue if past due date."""
    paid_total = sum(float(p.amount) for p in invoice.payments)
    if paid_total >= float(invoice.total_amount):
        invoice.status = "paid"
    elif invoice.due_date < date.today() and invoice.status not in ("paid", "cancelled"):
        invoice.status = "overdue"
