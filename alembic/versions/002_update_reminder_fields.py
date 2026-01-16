"""update_reminder_fields

Revision ID: 002_update_reminder_fields
Revises: 001_add_person_fields
Create Date: 2026-01-15 13:16:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_update_reminder_fields"
down_revision: Union[str, Sequence[str], None] = "001_add_person_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename due_time to reminder_time
    op.alter_column("reminders", "due_time", new_column_name="reminder_time")

    # Rename text to message
    op.alter_column("reminders", "text", new_column_name="message")

    # Add tags column
    op.add_column(
        "reminders",
        sa.Column("tags", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
    )

    # Drop old index
    op.drop_index(op.f("ix_reminders_due_time"), table_name="reminders")

    # Update composite index
    op.drop_index(op.f("ix_reminders_active"), table_name="reminders")
    op.create_index(
        "ix_reminders_active", "reminders", ["reminder_time", "is_completed"], unique=False
    )

    # Create new index
    op.create_index(
        op.f("ix_reminders_reminder_time"), "reminders", ["reminder_time"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new index
    op.drop_index(op.f("ix_reminders_reminder_time"), table_name="reminders")

    # Revert composite index
    op.drop_index("ix_reminders_active", table_name="reminders")

    # Remove tags column
    op.drop_column("reminders", "tags")

    # Rename message back to text
    op.alter_column("reminders", "message", new_column_name="text")

    # Rename reminder_time back to due_time
    op.alter_column("reminders", "reminder_time", new_column_name="due_time")

    # Recreate indexes AFTER columns are renamed
    op.create_index(
        op.f("ix_reminders_active"), "reminders", ["due_time", "is_completed"], unique=False
    )
    op.create_index(op.f("ix_reminders_due_time"), "reminders", ["due_time"], unique=False)
