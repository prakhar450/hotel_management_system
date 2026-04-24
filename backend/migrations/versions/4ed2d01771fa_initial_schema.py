"""initial schema

Revision ID: 4ed2d01771fa
Revises:
Create Date: 2026-04-25

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "4ed2d01771fa"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- guests ---
    op.create_table(
        "guests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("id_type", sa.String(50)),
        sa.Column("id_number", sa.String(100)),
        sa.Column("address", sa.Text),
        sa.Column("nationality", sa.String(100), server_default="Indian"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_guests_phone", "guests", ["phone"], unique=True)

    # --- rooms ---
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_number", sa.String(20), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("floor", sa.Integer, nullable=False),
        sa.Column("base_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(30), server_default="available"),
        sa.Column("amenities", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rooms_room_number", "rooms", ["room_number"], unique=True)

    # --- event_spaces ---
    op.create_table(
        "event_spaces",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False),
        sa.Column("base_rate_per_day", sa.Numeric(10, 2), nullable=False),
        sa.Column("base_rate_per_slot", sa.Numeric(10, 2), nullable=False),
        sa.Column("setup_time_hours", sa.Numeric(4, 1), server_default="2.0"),
        sa.Column("teardown_time_hours", sa.Numeric(4, 1), server_default="2.0"),
        sa.Column("amenities", postgresql.JSONB, server_default="{}"),
        sa.Column("status", sa.String(30), server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- inventory_items ---
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("total_quantity", sa.Integer, nullable=False),
        sa.Column("available_quantity", sa.Integer, nullable=False),
        sa.Column("low_stock_threshold", sa.Integer, server_default="10"),
        sa.Column("unit", sa.String(50), server_default="units"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- bookings ---
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False),
        sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("check_in", sa.Date, nullable=False),
        sa.Column("check_out", sa.Date, nullable=False),
        sa.Column("actual_checkin", sa.DateTime(timezone=True)),
        sa.Column("actual_checkout", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), server_default="confirmed"),
        sa.Column("adults", sa.Integer, server_default="1"),
        sa.Column("children", sa.Integer, server_default="0"),
        sa.Column("special_requests", sa.Text),
        sa.Column("source", sa.String(30), server_default="walk_in"),
        sa.Column("created_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bookings_room_dates", "bookings", ["room_id", "check_in", "check_out"])
    op.create_index("ix_bookings_guest_id", "bookings", ["guest_id"])

    # --- events ---
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False),
        sa.Column("space_id", sa.Integer, sa.ForeignKey("event_spaces.id"), nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("guest_count", sa.Integer, nullable=False),
        sa.Column("status", sa.String(30), server_default="confirmed"),
        sa.Column("special_requirements", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_space_date", "events", ["space_id", "event_date"])
    op.create_index("ix_events_guest_id", "events", ["guest_id"])

    # --- invoices ---
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_number", sa.String(30), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id")),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id")),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("line_items", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], unique=True)
    op.create_index("ix_invoices_booking_id", "invoices", ["booking_id"])
    op.create_index("ix_invoices_event_id", "invoices", ["event_id"])

    # --- payments ---
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("reference_number", sa.String(200)),
        sa.Column("recorded_by", sa.String(100)),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])

    # --- inventory_usage ---
    op.create_table(
        "inventory_usage",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("quantity_used", sa.Integer, nullable=False),
        sa.Column("return_date", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inventory_usage_event_id", "inventory_usage", ["event_id"])
    op.create_index("ix_inventory_usage_item_id", "inventory_usage", ["item_id"])

    # --- agent_logs ---
    op.create_table(
        "agent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("input_data", postgresql.JSONB, server_default="{}"),
        sa.Column("output_data", postgresql.JSONB, server_default="{}"),
        sa.Column("api_endpoint", sa.String(200)),
        sa.Column("success", sa.Boolean, server_default="true"),
        sa.Column("error_message", sa.Text),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_logs_agent_name", "agent_logs", ["agent_name"])
    op.create_index("ix_agent_logs_created_at", "agent_logs", ["created_at"])

    # --- tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("assigned_to_agent", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("context", postgresql.JSONB, server_default="{}"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_assigned_to_agent", "tasks", ["assigned_to_agent"])
    op.create_index("ix_tasks_status", "tasks", ["status"])

    # --- leads ---
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("event_type", sa.String(50)),
        sa.Column("event_date", sa.String(20)),
        sa.Column("guest_count", sa.Integer),
        sa.Column("budget_range", sa.String(100)),
        sa.Column("source", sa.String(50)),
        sa.Column("status", sa.String(30), server_default="new"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_leads_phone", "leads", ["phone"])
    op.create_index("ix_leads_status", "leads", ["status"])

    # --- quotes ---
    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("space_id", sa.Integer, sa.ForeignKey("event_spaces.id"), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("valid_until", sa.Date, nullable=False),
        sa.Column("line_items", postgresql.JSONB, server_default="[]"),
        sa.Column("status", sa.String(30), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quotes_lead_id", "quotes", ["lead_id"])


def downgrade() -> None:
    op.drop_table("quotes")
    op.drop_table("leads")
    op.drop_table("tasks")
    op.drop_table("agent_logs")
    op.drop_table("inventory_usage")
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("events")
    op.drop_table("bookings")
    op.drop_table("inventory_items")
    op.drop_table("event_spaces")
    op.drop_table("rooms")
    op.drop_table("guests")
