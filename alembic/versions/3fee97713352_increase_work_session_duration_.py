"""Increase work session duration precision to 2 decimals

Revision ID: 3fee97713352
Revises: 5b34a831393a
Create Date: 2026-01-21 07:26:59.764588

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3fee97713352"
down_revision: Union[str, Sequence[str], None] = "5b34a831393a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change duration_hours from Numeric(4,1) to Numeric(4,2) for exact durations
    op.alter_column(
        "work_sessions",
        "duration_hours",
        type_=sa.Numeric(4, 2),
        existing_type=sa.Numeric(4, 1),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Change duration_hours back from Numeric(4,2) to Numeric(4,1)
    op.alter_column(
        "work_sessions",
        "duration_hours",
        type_=sa.Numeric(4, 1),
        existing_type=sa.Numeric(4, 2),
        nullable=False,
    )
