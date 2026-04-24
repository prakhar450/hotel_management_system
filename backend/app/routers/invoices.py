from __future__ import annotations
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.invoice import InvoiceOut, PaymentCreate, PaymentOut
from app.services.invoice_service import update_invoice_status_on_payment

router = APIRouter(prefix="/api/v1", tags=["Invoices & Payments"])


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # Check overdue on read
    if invoice.due_date < date.today() and invoice.status == "sent":
        invoice.status = "overdue"
        db.commit()
    return invoice


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    status: str = None,
    db: Session = Depends(get_db),
):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    return q.order_by(Invoice.created_at.desc()).all()


@router.post("/payments", response_model=PaymentOut, status_code=201)
def record_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot record payment for a cancelled invoice")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    payment = Payment(
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
    q = db.query(Payment)
    if invoice_id:
        q = q.filter(Payment.invoice_id == invoice_id)
    return q.order_by(Payment.created_at.desc()).all()
