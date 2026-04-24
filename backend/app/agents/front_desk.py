from __future__ import annotations
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.booking import Booking
from app.models.guest import Guest
from app.models.room import Room
from app.services.booking_service import get_unavailable_room_ids

ESCALATE_THRESHOLD_INR = 50_000


class FrontDeskAgent(BaseAgent):
    name = "front_desk"
    system_prompt = """You are the Front Desk Agent for a hotel and wedding venue in India.
Your job: handle guest queries, check availability, confirm bookings, manage check-ins and check-outs.

Tone: warm, professional, and concise — like a well-trained hotel receptionist.

Rules:
- You can query availability and guest records. You never create bookings directly.
- If a booking value exceeds ₹50,000, or there is a guest complaint or overbooking risk, respond with ESCALATE: <reason>.
- Always address the guest by name if you know it.
- Keep responses under 3 sentences unless the guest asks a detailed question.
- Today's date is provided in context."""

    tools = [
        {
            "name": "check_room_availability",
            "description": "Check which rooms are available for a date range",
            "input_schema": {
                "type": "object",
                "properties": {
                    "check_in": {"type": "string", "description": "YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "YYYY-MM-DD"},
                    "room_type": {"type": "string", "description": "single/double/suite/deluxe (optional)"},
                },
                "required": ["check_in", "check_out"],
            },
        },
        {
            "name": "get_guest_by_phone",
            "description": "Look up a guest by phone number",
            "input_schema": {
                "type": "object",
                "properties": {"phone": {"type": "string"}},
                "required": ["phone"],
            },
        },
        {
            "name": "get_booking_details",
            "description": "Get details of a booking by ID",
            "input_schema": {
                "type": "object",
                "properties": {"booking_id": {"type": "string"}},
                "required": ["booking_id"],
            },
        },
    ]

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        if tool_name == "check_room_availability":
            check_in = date.fromisoformat(tool_input["check_in"])
            check_out = date.fromisoformat(tool_input["check_out"])
            unavailable = get_unavailable_room_ids(db, check_in, check_out)
            q = db.query(Room).filter(
                Room.status.notin_(["maintenance", "blocked"]),
                Room.id.notin_(unavailable),
            )
            if tool_input.get("room_type"):
                q = q.filter(Room.type == tool_input["room_type"])
            rooms = q.all()
            if not rooms:
                return "No rooms available for those dates."
            return [
                {"room_number": r.room_number, "type": r.type, "rate_per_night": float(r.base_rate)}
                for r in rooms
            ]

        if tool_name == "get_guest_by_phone":
            guest = db.query(Guest).filter(Guest.phone == tool_input["phone"]).first()
            if not guest:
                return "Guest not found"
            return {"name": guest.name, "phone": guest.phone, "email": guest.email, "id": str(guest.id)}

        if tool_name == "get_booking_details":
            import uuid as _uuid
            booking = db.query(Booking).filter(Booking.id == _uuid.UUID(tool_input["booking_id"])).first()
            if not booking:
                return "Booking not found"
            return {
                "id": str(booking.id), "status": booking.status,
                "check_in": str(booking.check_in), "check_out": str(booking.check_out),
                "room_id": booking.room_id, "adults": booking.adults,
            }

        return f"Unknown tool: {tool_name}"
