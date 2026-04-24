from __future__ import annotations
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.room import Room
from app.models.inventory_item import InventoryItem
from app.models.event import Event


class InventoryAgent(BaseAgent):
    name = "inventory"
    system_prompt = """You are the Inventory Agent for a hotel and wedding venue in India.
Your job: track room status, event space availability, and consumable stock levels.

Tone: matter-of-fact. Return structured data with a plain-language summary.

Rules:
- You never modify stock counts directly. You report and flag.
- If consumable stock falls below threshold, flag it clearly.
- If a hall conflict is detected, respond with ESCALATE: <reason>.
- For events with large guest counts, proactively check if stock is sufficient."""

    tools = [
        {
            "name": "get_room_status_summary",
            "description": "Get a summary of all room statuses",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "check_stock_levels",
            "description": "Get current stock for all consumable items, flagging low stock",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "check_stock_for_event",
            "description": "Check if stock is sufficient for an event with a given guest count",
            "input_schema": {
                "type": "object",
                "properties": {
                    "guest_count": {"type": "integer"},
                    "event_date": {"type": "string"},
                },
                "required": ["guest_count"],
            },
        },
        {
            "name": "upcoming_events_scan",
            "description": "List upcoming events in the next N days",
            "input_schema": {
                "type": "object",
                "properties": {"days": {"type": "integer", "default": 7}},
                "required": [],
            },
        },
    ]

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        if tool_name == "get_room_status_summary":
            rooms = db.query(Room).all()
            summary: dict = {"available": 0, "occupied": 0, "maintenance": 0, "blocked": 0}
            for r in rooms:
                summary[r.status] = summary.get(r.status, 0) + 1
            return summary

        if tool_name == "check_stock_levels":
            items = db.query(InventoryItem).all()
            return [
                {
                    "name": i.name, "category": i.category,
                    "available": i.available_quantity, "total": i.total_quantity,
                    "unit": i.unit, "low_stock": i.available_quantity <= i.low_stock_threshold,
                }
                for i in items
            ]

        if tool_name == "check_stock_for_event":
            guest_count = tool_input["guest_count"]
            items = db.query(InventoryItem).all()
            issues = []
            # Key items to check against guest count
            key_items = {"Banquet Chairs": 1, "Dinner Plates": 1, "Water Glasses": 1}
            for item in items:
                if item.name in key_items:
                    needed = guest_count * key_items[item.name]
                    if item.available_quantity < needed:
                        issues.append({
                            "item": item.name,
                            "needed": needed,
                            "available": item.available_quantity,
                            "shortfall": needed - item.available_quantity,
                        })
            if issues:
                return {"status": "insufficient_stock", "issues": issues}
            return {"status": "stock_ok", "guest_count": guest_count}

        if tool_name == "upcoming_events_scan":
            days = tool_input.get("days", 7)
            today = date.today()
            events = db.query(Event).filter(
                Event.event_date >= today,
                Event.event_date <= today + timedelta(days=days),
                Event.status.notin_(["cancelled"]),
            ).all()
            return [
                {"name": e.name, "date": str(e.event_date),
                 "guest_count": e.guest_count, "type": e.event_type}
                for e in events
            ]

        return f"Unknown tool: {tool_name}"
