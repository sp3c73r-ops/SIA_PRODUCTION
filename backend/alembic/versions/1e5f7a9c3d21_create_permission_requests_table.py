"""create permission requests table

Revision ID: 1e5f7a9c3d21
Revises: f1a7c9e2b4d6
Create Date: 2026-08-30 10:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1e5f7a9c3d21"
down_revision: Union[str, Sequence[str], None] = "f1a7c9e2b4d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permission_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bureau_id", sa.Integer(), nullable=False),
        sa.Column("permission", sa.String(length=120), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["bureau_id"], ["bureaux.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_permission_requests_id",
        "permission_requests",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_permission_requests_user_id",
        "permission_requests",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_permission_requests_bureau_id",
        "permission_requests",
        ["bureau_id"],
        unique=False,
    )

    op.create_index(
        "ix_permission_requests_status",
        "permission_requests",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_permission_requests_permission",
        "permission_requests",
        ["permission"],
        unique=False,
    )

    op.create_index(
        "ix_permission_requests_document_id",
        "permission_requests",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_permission_requests_document_id",
        table_name="permission_requests",
    )

    op.drop_index(
        "ix_permission_requests_permission",
        table_name="permission_requests",
    )

    op.drop_index(
        "ix_permission_requests_status",
        table_name="permission_requests",
    )

    op.drop_index(
        "ix_permission_requests_bureau_id",
        table_name="permission_requests",
    )

    op.drop_index(
        "ix_permission_requests_user_id",
        table_name="permission_requests",
    )

    op.drop_index(
        "ix_permission_requests_id",
        table_name="permission_requests",
    )

    op.drop_table("permission_requests")
