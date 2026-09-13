"""add circonscription to bureaux

Revision ID: 0a7d3b4c9e20
Revises: 1e5f7a9c3d21
Create Date: 2026-09-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a7d3b4c9e20"
down_revision: Union[str, Sequence[str], None] = "1e5f7a9c3d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bureaux",
        sa.Column(
            "circonscription_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_bureaux_circonscription",
        "bureaux",
        "circonscriptions",
        ["circonscription_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_bureaux_circonscription_id",
        "bureaux",
        ["circonscription_id"],
        unique=False,
    )

    op.drop_constraint(
        "bureaux_code_key",
        "bureaux",
        type_="unique",
    )

    op.drop_constraint(
        "bureaux_nom_key",
        "bureaux",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_bureaux_circonscription_code",
        "bureaux",
        ["circonscription_id", "code"],
    )

    op.create_unique_constraint(
        "uq_bureaux_circonscription_nom",
        "bureaux",
        ["circonscription_id", "nom"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_bureaux_circonscription_nom",
        "bureaux",
        type_="unique",
    )

    op.drop_constraint(
        "uq_bureaux_circonscription_code",
        "bureaux",
        type_="unique",
    )

    op.create_unique_constraint(
        "bureaux_nom_key",
        "bureaux",
        ["nom"],
    )

    op.create_unique_constraint(
        "bureaux_code_key",
        "bureaux",
        ["code"],
    )

    op.drop_index(
        "ix_bureaux_circonscription_id",
        table_name="bureaux",
    )

    op.drop_constraint(
        "fk_bureaux_circonscription",
        "bureaux",
        type_="foreignkey",
    )

    op.drop_column(
        "bureaux",
        "circonscription_id",
    )
