from __future__ import annotations
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.agents.orchestrator import invoke_agent
from app.models.agent_log import AgentLog

router = APIRouter(prefix="/api/v1/agent", tags=["Agents"])

# Message type colours used by the frontend chat UI
MESSAGE_TYPE_META = {
    "user_request": {"color": "#6366f1", "label": "Request"},
    "tool_call":    {"color": "#f59e0b", "label": "Checking..."},
    "tool_result":  {"color": "#10b981", "label": "Data"},
    "response":     {"color": "#3b82f6", "label": "Response"},
    "escalation":   {"color": "#ef4444", "label": "Escalation"},
}


class InvokeRequest(BaseModel):
    agent_name: str
    task: str
    context: Optional[dict] = {}


class InvokeResponse(BaseModel):
    agent_name: str
    response: str
    escalated: bool
    escalated_from: Optional[str] = None
    escalation_reason: Optional[str] = None
    conversation_id: str


@router.post("/invoke", response_model=InvokeResponse)
def invoke(data: InvokeRequest, db: Session = Depends(get_db)):
    context = data.context or {}
    context.setdefault("today", str(date.today()))
    result = invoke_agent(data.agent_name, data.task, context, db)
    return InvokeResponse(**result)


@router.get("/logs")
def agent_logs(
    agent_name: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """Flat log feed for the activity sidebar."""
    q = db.query(AgentLog).order_by(AgentLog.created_at.desc())
    if agent_name:
        q = q.filter(AgentLog.agent_name == agent_name)
    total = q.count()
    logs = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "logs": [_format_log(log) for log in logs],
    }


@router.get("/conversations")
def conversations(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """Return a list of recent conversations (one entry per conversation_id)."""
    # Get the latest request log per conversation
    from sqlalchemy import func
    subq = (
        db.query(
            AgentLog.conversation_id,
            func.max(AgentLog.created_at).label("latest"),
        )
        .filter(AgentLog.conversation_id.isnot(None))
        .group_by(AgentLog.conversation_id)
        .order_by(func.max(AgentLog.created_at).desc())
        .limit(limit)
        .subquery()
    )
    rows = (
        db.query(AgentLog)
        .join(subq, (AgentLog.conversation_id == subq.c.conversation_id) &
                    (AgentLog.created_at == subq.c.latest))
        .all()
    )
    return [
        {
            "conversation_id": str(r.conversation_id),
            "agent_name": r.agent_name,
            "summary": r.action,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]


@router.get("/conversations/{conversation_id}")
def conversation_thread(conversation_id: str, db: Session = Depends(get_db)):
    """
    Return all messages in a conversation as an ordered thread —
    ready to render as a team chat.
    """
    import uuid as _uuid
    try:
        cid = _uuid.UUID(conversation_id)
    except ValueError:
        return {"messages": []}

    logs = (
        db.query(AgentLog)
        .filter(AgentLog.conversation_id == cid)
        .order_by(AgentLog.step_order, AgentLog.created_at)
        .all()
    )

    return {
        "conversation_id": conversation_id,
        "messages": [_format_log(log) for log in logs],
    }


def _format_log(log: AgentLog) -> dict:
    meta = MESSAGE_TYPE_META.get(log.message_type, {"color": "#94a3b8", "label": log.message_type})
    return {
        "id": str(log.id),
        "conversation_id": str(log.conversation_id) if log.conversation_id else None,
        "sender": log.sender_label or log.agent_name,
        "message_type": log.message_type,
        "type_label": meta["label"],
        "bubble_color": meta["color"],
        "step_order": log.step_order,
        "action": log.action,
        "content": log.output_data.get("response") or log.output_data.get("result") or log.action,
        "input_data": log.input_data,
        "success": log.success,
        "duration_ms": log.duration_ms,
        "timestamp": str(log.created_at),
    }
