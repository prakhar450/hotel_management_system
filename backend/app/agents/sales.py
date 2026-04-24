from __future__ import annotations
from datetime import date, timedelta, timezone, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.lead import Lead
from app.models.event_space import EventSpace

ESCALATE_DEAL_VALUE_INR = 200_000


class SalesAgent(BaseAgent):
    name = "sales"
    system_prompt = """You are the Sales Agent for a hotel and wedding venue in India.
Your job: manage wedding and event leads, suggest follow-up actions, and help with quotes.

Tone: enthusiastic but not pushy — like a skilled sales coordinator.

Rules:
- You never set prices. You use the rates defined in the system.
- If a deal value exceeds ₹2,00,000 or a client requests custom pricing, respond with ESCALATE: <reason>.
- Always suggest a concrete next action for each lead (call, site visit, send quote).
- Flag leads that haven't been contacted in more than 3 days."""

    tools = [
        {
            "name": "list_leads_needing_followup",
            "description": "Get leads that haven't been contacted recently or are in early stages",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_lead_details",
            "description": "Get full details of a specific lead",
            "input_schema": {
                "type": "object",
                "properties": {"lead_id": {"type": "string"}},
                "required": ["lead_id"],
            },
        },
        {
            "name": "get_space_rates",
            "description": "Get event space rates for quoting",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
    ]

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        if tool_name == "list_leads_needing_followup":
            cutoff = datetime.now(timezone.utc) - timedelta(days=3)
            leads = db.query(Lead).filter(
                Lead.status.notin_(["won", "lost"]),
            ).all()
            result = []
            for lead in leads:
                days_since = None
                if lead.last_contacted_at:
                    days_since = (datetime.now(timezone.utc) - lead.last_contacted_at).days
                result.append({
                    "id": str(lead.id), "name": lead.name, "phone": lead.phone,
                    "status": lead.status, "event_type": lead.event_type,
                    "event_date": lead.event_date, "budget_range": lead.budget_range,
                    "days_since_contact": days_since,
                    "needs_followup": days_since is None or days_since >= 3,
                })
            return result

        if tool_name == "get_lead_details":
            import uuid as _uuid
            lead = db.query(Lead).filter(Lead.id == _uuid.UUID(tool_input["lead_id"])).first()
            if not lead:
                return "Lead not found"
            return {
                "name": lead.name, "phone": lead.phone, "email": lead.email,
                "event_type": lead.event_type, "event_date": lead.event_date,
                "guest_count": lead.guest_count, "budget_range": lead.budget_range,
                "status": lead.status, "notes": lead.notes,
            }

        if tool_name == "get_space_rates":
            spaces = db.query(EventSpace).filter(EventSpace.status == "available").all()
            return [
                {"name": s.name, "type": s.type, "capacity": s.capacity,
                 "rate_per_day": float(s.base_rate_per_day),
                 "rate_per_slot": float(s.base_rate_per_slot)}
                for s in spaces
            ]

        return f"Unknown tool: {tool_name}"
