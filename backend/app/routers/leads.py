from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate, LeadOut

router = APIRouter(prefix="/api/v1/leads", tags=["Leads"])


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(id=uuid.uuid4(), **data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=list[LeadOut])
def list_leads(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Lead)
    if status:
        q = q.filter(Lead.status == status)
    return q.order_by(Lead.created_at.desc()).all()


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: uuid.UUID, data: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    lead.last_contacted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(lead)
    return lead
