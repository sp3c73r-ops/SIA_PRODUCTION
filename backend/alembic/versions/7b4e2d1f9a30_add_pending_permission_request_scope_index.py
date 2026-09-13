"""add pending permission request scope index

Revision ID: 7b4e2d1f9a30
Revises: e8b3f1a7c2d4
Create Date: 2026-09-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "7b4e2d1f9a30"
down_revision: Union[str, Sequence[str], None] = "e8b3f1a7c2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_permission_requests_pending_scope",
        "permission_requests",
        ["user_id", "permission", "document_id"],
        unique=True,
        postgresql_where=(
            "status = 'PENDING' AND document_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_permission_requests_pending_scope",
        table_name="permission_requests",
    )
