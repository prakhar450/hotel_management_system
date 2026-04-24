from datetime import date
from sqlalchemy.orm import Session


def next_invoice_number(db: Session) -> str:
    """Generate INV-YYYY-NNNN — sequential within the year, never repeats."""
    from app.models.invoice import Invoice

    year = date.today().year
    prefix = f"INV-{year}-"

    last = (
        db.query(Invoice.invoice_number)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    if last:
        seq = int(last[0].split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"
