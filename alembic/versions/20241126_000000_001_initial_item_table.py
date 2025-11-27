"""Initial Item table migration.

Revision ID: 001
Revises: None
Create Date: 2024-11-26 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create items table."""
    op.create_table(
        "items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("tax", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create index for soft delete queries
    op.create_index("ix_items_is_deleted", "items", ["is_deleted"])
    # Create index for name searches
    op.create_index("ix_items_name", "items", ["name"])


def downgrade() -> None:
    """Drop items table."""
    op.drop_index("ix_items_name", table_name="items")
    op.drop_index("ix_items_is_deleted", table_name="items")
    op.drop_table("items")
