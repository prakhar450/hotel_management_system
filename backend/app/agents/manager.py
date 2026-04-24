from __future__ import annotations
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.booking import Booking
from app.models.event import Event
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.room import Room
from app.models.inventory_item import InventoryItem


class ManagerAgent(BaseAgent):
    name = "manager"
    system_prompt = """You are the General Manager Agent for a hotel and wedding venue in India.
Your job: review escalations, approve decisions, generate daily briefings, and see the full picture.

Tone: executive — summarise clearly, decide quickly, delegate where appropriate.

Rules:
- You have read access to everything. You can approve or flag for human action.
- For the daily briefing, be concise: occupancy, revenue, key events, top alerts.
- When handling an escalation, state your decision clearly: APPROVED, REJECTED, or NEEDS_HUMAN.
- Always end with one actionable next step."""

    tools = [
        {
            "name": "get_full_daily_summary",
            "description": "Get today's occupancy, revenue, check-ins, check-outs, events, and alerts",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_pending_escalations",
            "description": "Get a list of high-value or flagged items needing manager attention",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_revenue_summary",
            "description": "Get revenue breakdown for today and this month",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
    ]

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        today = date.today()

        if tool_name == "get_full_daily_summary":
            checkins = db.query(Booking).filter(
                Booking.check_in == today, Booking.status == "confirmed"
            ).count()
            checkouts = db.query(Booking).filter(
                Booking.check_out == today, Booking.status == "checked_in"
            ).count()
            active_events = db.query(Event).filter(
                Event.event_date == today, Event.status.notin_(["cancelled"])
            ).all()
            upcoming = db.query(Event).filter(
                Event.event_date > today,
                Event.event_date <= today + timedelta(days=7),
                Event.status.notin_(["cancelled"]),
            ).count()
            total_rooms = db.query(Room).count()
            occupied = db.query(Room).filter(Room.status == "occupied").count()
            revenue_today = db.query(func.sum(Payment.amount)).filter(
                Payment.payment_date == today
            ).scalar() or 0
            low_stock = db.query(InventoryItem).filter(
                InventoryItem.available_quantity <= InventoryItem.low_stock_threshold
            ).count()
            overdue_invoices = db.query(Invoice).filter(
                Invoice.due_date < today, Invoice.status.in_(["sent", "overdue"])
            ).count()

            return {
                "date": str(today),
                "occupancy": f"{occupied}/{total_rooms} rooms ({round(occupied/total_rooms*100) if total_rooms else 0}%)",
                "checkins_today": checkins,
                "checkouts_today": checkouts,
                "active_events": [{"name": e.name, "guests": e.guest_count} for e in active_events],
                "upcoming_events_7d": upcoming,
                "revenue_today_inr": float(revenue_today),
                "alerts": {
                    "low_stock_items": low_stock,
                    "overdue_invoices": overdue_invoices,
                },
            }

        if tool_name == "get_pending_escalations":
            # High-value invoices not yet paid
            high_value = db.query(Invoice).filter(
                Invoice.total_amount >= 50000,
                Invoice.status.in_(["sent", "overdue"]),
            ).all()
            overdue = db.query(Invoice).filter(
                Invoice.due_date < today,
                Invoice.status.in_(["sent", "overdue"]),
            ).all()
            return {
                "high_value_unpaid": [
                    {"invoice": inv.invoice_number, "amount": float(inv.total_amount), "due": str(inv.due_date)}
                    for inv in high_value
                ],
                "overdue_invoices": len(overdue),
            }

        if tool_name == "get_revenue_summary":
            month_start = today.replace(day=1)
            revenue_today = db.query(func.sum(Payment.amount)).filter(
                Payment.payment_date == today
            ).scalar() or 0
            revenue_month = db.query(func.sum(Payment.amount)).filter(
                Payment.payment_date >= month_start
            ).scalar() or 0
            return {
                "revenue_today_inr": float(revenue_today),
                "revenue_this_month_inr": float(revenue_month),
                "month": today.strftime("%B %Y"),
            }

        return f"Unknown tool: {tool_name}"
