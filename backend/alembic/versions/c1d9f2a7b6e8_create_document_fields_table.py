"""create_document_fields_table

Revision ID: c1d9f2a7b6e8
Revises: c8e4eec8b45a
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d9f2a7b6e8"
down_revision: Union[str, Sequence[str], None] = "c8e4eec8b45a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False),
        sa.Column("field_type", sa.String(length=30), nullable=False, server_default="string"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_document_fields_id"), "document_fields", ["id"], unique=False)
    op.create_index(op.f("ix_document_fields_name"), "document_fields", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_fields_name"), table_name="document_fields")
    op.drop_index(op.f("ix_document_fields_id"), table_name="document_fields")
    op.drop_table("document_fields")
