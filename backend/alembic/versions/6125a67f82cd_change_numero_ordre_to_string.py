"""change numero ordre to string

Revision ID: 6125a67f82cd
Revises: c8e4eec8b45a
Create Date: 2026-08-11 01:32:49.199950

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "6125a67f82cd"
down_revision: Union[str, Sequence[str], None] = "c8e4eec8b45a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "documents",
        "numero_ordre",
        existing_type=sa.Integer(),
        type_=sa.String(length=100),
        existing_nullable=True,
        postgresql_using="numero_ordre::varchar",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "documents",
        "numero_ordre",
        existing_type=sa.String(length=100),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="numero_ordre::integer",
    )