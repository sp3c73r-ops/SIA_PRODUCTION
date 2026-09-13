"""create audit logs table

Revision ID: 8c5f3e2d1a40
Revises: 7b4e2d1f9a30
Create Date: 2026-09-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8c5f3e2d1a40"
down_revision: Union[str, Sequence[str], None] = "7b4e2d1f9a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("permission_request_id", sa.Integer(), nullable=True),
        sa.Column("bureau_id", sa.Integer(), nullable=True),
        sa.Column("circonscription_id", sa.Integer(), nullable=True),
        sa.Column(
            "old_state",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "new_state",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["bureau_id"],
            ["bureaux.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["permission_request_id"],
            ["permission_requests.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_actor_user_id"),
        "audit_logs",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_document_id"),
        "audit_logs",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_permission_request_id"),
        "audit_logs",
        ["permission_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_bureau_id"),
        "audit_logs",
        ["bureau_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_circonscription_id"),
        "audit_logs",
        ["circonscription_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_created_at"),
        "audit_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index(
        op.f("ix_audit_logs_created_at"), table_name="audit_logs"
    )
    op.drop_index(
        op.f("ix_audit_logs_circonscription_id"), table_name="audit_logs"
    )
    op.drop_index(
        op.f("ix_audit_logs_bureau_id"), table_name="audit_logs"
    )
    op.drop_index(
        op.f("ix_audit_logs_permission_request_id"), table_name="audit_logs"
    )
    op.drop_index(
        op.f("ix_audit_logs_document_id"), table_name="audit_logs"
    )
    op.drop_index(
        op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs"
    )
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
