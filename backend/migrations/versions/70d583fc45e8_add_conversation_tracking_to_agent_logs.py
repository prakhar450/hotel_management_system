"""add conversation tracking to agent logs

Revision ID: 70d583fc45e8
Revises: 4ed2d01771fa
Create Date: 2026-04-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "70d583fc45e8"
down_revision: Union[str, None] = "4ed2d01771fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agent_logs", sa.Column(
        "conversation_id", postgresql.UUID(as_uuid=True), nullable=True
    ))
    op.add_column("agent_logs", sa.Column(
        "message_type", sa.String(30), nullable=True, server_default="response"
    ))
    op.add_column("agent_logs", sa.Column(
        "step_order", sa.Integer, nullable=True, server_default="0"
    ))
    op.add_column("agent_logs", sa.Column(
        "sender_label", sa.String(100), nullable=True
    ))
    op.create_index("ix_agent_logs_conversation_id", "agent_logs", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_logs_conversation_id", "agent_logs")
    op.drop_column("agent_logs", "sender_label")
    op.drop_column("agent_logs", "step_order")
    op.drop_column("agent_logs", "message_type")
    op.drop_column("agent_logs", "conversation_id")
