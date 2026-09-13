"""create notifications table

Revision ID: 9d6e4f3a2b10
Revises: 8c5f3e2d1a40
Create Date: 2026-09-13 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d6e4f3a2b10"
down_revision: Union[str, Sequence[str], None] = "8c5f3e2d1a40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("permission_request_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("bureau_id", sa.Integer(), nullable=True),
        sa.Column("circonscription_id", sa.Integer(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_request_id"],
            ["permission_requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_notifications_permission_request_id"),
        "notifications",
        ["permission_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_document_id"),
        "notifications",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_bureau_id"),
        "notifications",
        ["bureau_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_circonscription_id"),
        "notifications",
        ["circonscription_id"],
        unique=False,
    )
    # Index composite pour les recherches rapides du destinataire / filtres lu/non lu et tri chronologique
    op.create_index(
        "ix_notifications_recipient_read_created",
        "notifications",
        ["recipient_user_id", "read_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notifications_recipient_read_created", table_name="notifications"
    )
    op.drop_index(
        op.f("ix_notifications_circonscription_id"), table_name="notifications"
    )
    op.drop_index(
        op.f("ix_notifications_bureau_id"), table_name="notifications"
    )
    op.drop_index(
        op.f("ix_notifications_document_id"), table_name="notifications"
    )
    op.drop_index(
        op.f("ix_notifications_permission_request_id"),
        table_name="notifications",
    )
    op.drop_table("notifications")
