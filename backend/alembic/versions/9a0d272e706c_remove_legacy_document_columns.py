"""remove legacy document columns

Revision ID: 9a0d272e706c
Revises: 6125a67f82cd
Create Date: 2026-08-11 01:47:05.904352

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "9a0d272e706c"
down_revision: Union[str, Sequence[str], None] = "6125a67f82cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_column("documents", "type_document")
    op.drop_column("documents", "phase_enregistrement")
    op.drop_column("documents", "circo_fonciere")
    op.drop_column("documents", "encodeur")


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "documents",
        sa.Column(
            "type_document",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "phase_enregistrement",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "circo_fonciere",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "encodeur",
            sa.String(length=150),
            nullable=True,
        ),
    )