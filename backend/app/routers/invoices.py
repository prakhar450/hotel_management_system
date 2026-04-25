from __future__ import annotations
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.models.guest import Guest
from app.models.invoice import Invoice
from app.models.payment import Payment as PaymentModel
from app.schemas.invoice import InvoiceOut, PaymentCreate, PaymentOut
from app.services.invoice_service import update_invoice_status_on_payment

router = APIRouter(prefix="/api/v1", tags=["Invoices & Payments"])


def _invoice_to_dict(inv: Invoice, db: Session, include_payments: bool = False) -> dict:
    guest_name = None
    if inv.booking_id:
        booking = db.query(Booking).filter(Booking.id == inv.booking_id).first()
        if booking:
            guest = db.query(Guest).filter(Guest.id == booking.guest_id).first()
            if guest:
                guest_name = guest.name
    payments = db.query(PaymentModel).filter(PaymentModel.invoice_id == inv.id).all()
    paid_amount = sum(p.amount for p in payments)
    d = {
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "booking_id": str(inv.booking_id) if inv.booking_id else None,
        "event_id": str(inv.event_id) if inv.event_id else None,
        "subtotal": float(inv.subtotal),
        "tax_amount": float(inv.tax_amount),
        "discount_amount": float(inv.discount_amount),
        "total_amount": float(inv.total_amount),
        "status": inv.status,
        "due_date": str(inv.due_date),
        "line_items": inv.line_items,
        "created_at": str(inv.created_at),
        "guest_name": guest_name,
        "paid_amount": float(paid_amount),
        "issued_date": str(inv.created_at.date()),
    }
    if include_payments:
        d["payments"] = [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "payment_mode": p.method,
                "payment_date": str(p.payment_date),
            }
            for p in payments
        ]
    return d


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # Check overdue on read
    if invoice.due_date < date.today() and invoice.status == "sent":
        invoice.status = "overdue"
        db.commit()
    return _invoice_to_dict(invoice, db, include_payments=True)


@router.get("/invoices")
def list_invoices(
    status: str = None,
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    invoices = q.order_by(Invoice.created_at.desc()).all()
    return [_invoice_to_dict(inv, db) for inv in invoices]


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot record payment for a cancelled invoice")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    payment = PaymentModel(
        id=uuid.uuid4(),
        invoice_id=data.invoice_id,
        amount=data.amount,
        method=data.method,
        reference_number=data.reference_number,
        payment_date=data.payment_date,
        notes=data.notes,
    )
    db.add(payment)
    db.flush()

    db.refresh(invoice)
    update_invoice_status_on_payment(db, invoice)

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    invoice_id: uuid.UUID = None,
    db: Session = Depends(get_db),
):
    q = db.query(PaymentModel)
    if invoice_id:
        q = q.filter(PaymentModel.invoice_id == invoice_id)
    return q.order_by(PaymentModel.created_at.desc()).all()
