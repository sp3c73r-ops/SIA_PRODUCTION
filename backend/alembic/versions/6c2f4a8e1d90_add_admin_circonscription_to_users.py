"""add admin circonscription to users

Revision ID: 6c2f4a8e1d90
Revises: 0a7d3b4c9e20
Create Date: 2026-09-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c2f4a8e1d90"
down_revision: Union[str, Sequence[str], None] = "0a7d3b4c9e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "admin_circonscription_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_users_admin_circonscription",
        "users",
        "circonscriptions",
        ["admin_circonscription_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_users_admin_circonscription_id",
        "users",
        ["admin_circonscription_id"],
        unique=False,
    )

    op.create_index(
        "uq_users_one_admin_per_circonscription",
        "users",
        ["admin_circonscription_id"],
        unique=True,
        postgresql_where=sa.text("role = 'ADMIN'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_users_one_admin_per_circonscription",
        table_name="users",
    )

    op.drop_index(
        "ix_users_admin_circonscription_id",
        table_name="users",
    )

    op.drop_constraint(
        "fk_users_admin_circonscription",
        "users",
        type_="foreignkey",
    )

    op.drop_column(
        "users",
        "admin_circonscription_id",
    )
