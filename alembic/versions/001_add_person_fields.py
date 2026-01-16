"""add_person_fields

Revision ID: 001_add_person_fields
Revises: ef648c8126f5
Create Date: 2026-01-15 13:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_add_person_fields"
down_revision: Union[str, Sequence[str], None] = "ef648c8126f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new fields to Person model
    op.add_column("people", sa.Column("company", sa.String(length=200), nullable=True))
    op.add_column("people", sa.Column("title", sa.String(length=200), nullable=True))
    op.add_column("people", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "people",
        sa.Column("tags", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove fields from Person model
    op.drop_column("people", "tags")
    op.drop_column("people", "notes")
    op.drop_column("people", "title")
    op.drop_column("people", "company")
