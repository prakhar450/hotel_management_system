"""make events guest_id nullable

Revision ID: 1b84d9554ee7
Revises: 70d583fc45e8
Create Date: 2026-04-25 15:54:59.768767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1b84d9554ee7'
down_revision: Union[str, None] = '70d583fc45e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("events", "guest_id", nullable=True)


def downgrade() -> None:
    op.alter_column("events", "guest_id", nullable=False)
