"""create document field values table

Revision ID: b7d6a0f9c2e1
Revises: 3abfbc257bf0
Create Date: 2026-08-23 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d6a0f9c2e1"
down_revision: Union[str, Sequence[str], None] = "3abfbc257bf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_field_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_field_id", sa.Integer(), nullable=False),
        sa.Column("value_string", sa.String(length=255), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_integer", sa.Integer(), nullable=True),
        sa.Column("value_decimal", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("value_datetime", sa.DateTime(timezone=False), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["document_field_id"], ["document_fields.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "document_field_id",
            name="uq_document_field_values_document_field",
        ),
    )
    op.create_index(
        op.f("ix_document_field_values_id"),
        "document_field_values",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_field_values_document_id"),
        "document_field_values",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_field_values_document_field_id"),
        "document_field_values",
        ["document_field_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_field_values_document_field_id"), table_name="document_field_values")
    op.drop_index(op.f("ix_document_field_values_document_id"), table_name="document_field_values")
    op.drop_index(op.f("ix_document_field_values_id"), table_name="document_field_values")
    op.drop_table("document_field_values")
