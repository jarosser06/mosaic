"""update_client_contact

Revision ID: 003_update_client_contact
Revises: 002_update_reminder_fields
Create Date: 2026-01-15 13:17:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_update_client_contact"
down_revision: Union[str, Sequence[str], None] = "002_update_reminder_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add contact_person_id foreign key
    op.add_column("clients", sa.Column("contact_person_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_clients_contact_person_id",
        "clients",
        "people",
        ["contact_person_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add tags column
    op.add_column(
        "clients",
        sa.Column("tags", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
    )

    # Drop old contact_info column
    op.drop_column("clients", "contact_info")


def downgrade() -> None:
    """Downgrade schema."""
    # Restore contact_info column
    op.add_column(
        "clients",
        sa.Column("contact_info", sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    )

    # Remove tags column
    op.drop_column("clients", "tags")

    # Remove foreign key and column
    op.drop_constraint("fk_clients_contact_person_id", "clients", type_="foreignkey")
    op.drop_column("clients", "contact_person_id")
