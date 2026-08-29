"""add role and permissions to users

Revision ID: d2f6c1a9e4b3
Revises: 4c07674d4dda
Create Date: 2026-08-28 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d2f6c1a9e4b3"
down_revision: Union[str, Sequence[str], None] = "4c07674d4dda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=True,
            server_default=sa.text("'USER'"),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.execute(
        sa.text(
            "UPDATE users SET role = 'USER' WHERE role IS NULL"
        )
    )

    op.execute(
        sa.text(
            "UPDATE users SET role = 'ADMIN' WHERE username = 'sia.manager'"
        )
    )

    op.execute(
        sa.text(
            "UPDATE users SET permissions = '[]'::jsonb WHERE permissions IS NULL"
        )
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=20),
        nullable=False,
        existing_server_default=sa.text("'USER'"),
    )


def downgrade() -> None:
    op.drop_column(
        "users",
        "permissions",
    )

    op.drop_column(
        "users",
        "role",
    )