"""Remove start_time and end_time from work_session

Revision ID: 5b34a831393a
Revises: 5a8b13d16ac1
Create Date: 2026-01-20 19:30:15.646568

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b34a831393a"
down_revision: Union[str, Sequence[str], None] = "5a8b13d16ac1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Remove start_time and end_time from work_sessions."""
    # Drop start_time and end_time columns
    op.drop_column("work_sessions", "start_time")
    op.drop_column("work_sessions", "end_time")


def downgrade() -> None:
    """Downgrade schema: Add back start_time and end_time columns."""
    # Add columns back (data will be lost)
    op.add_column(
        "work_sessions",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("work_sessions", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True))
