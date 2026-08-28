"""create attachments and movements tables

Revision ID: c8e4eec8b45a
Revises: 856dd8b9b901
Create Date: 2026-08-10 06:44:12.107690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "c8e4eec8b45a"
down_revision: Union[str, Sequence[str], None] = "856dd8b9b901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ============================================================
    # PIÈCES JOINTES
    # ============================================================

    op.create_table(
        "document_attachments",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "nom_original",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "nom_stockage",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "chemin_fichier",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "type_mime",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "taille",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
    )

    # ============================================================
    # MOUVEMENTS
    # ============================================================

    op.create_table(
        "movements",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "type_mouvement",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "motif",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "statut",
            sa.String(length=30),
            server_default=sa.text("'EN_COURS'"),
            nullable=False,
        ),
        sa.Column(
            "date_mouvement",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "date_retour",
            sa.DateTime(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_movements_document",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_movements_user",
            ondelete="RESTRICT",
        ),
    )

    # ============================================================
    # INDEX DES MOUVEMENTS
    # ============================================================

    op.create_index(
        "ix_movements_document_id",
        "movements",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        "ix_movements_user_id",
        "movements",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_movements_statut",
        "movements",
        ["statut"],
        unique=False,
    )

    op.create_index(
        "ix_movements_date_mouvement",
        "movements",
        ["date_mouvement"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Supprimer les index avant la table
    op.drop_index(
        "ix_movements_date_mouvement",
        table_name="movements",
    )

    op.drop_index(
        "ix_movements_statut",
        table_name="movements",
    )

    op.drop_index(
        "ix_movements_user_id",
        table_name="movements",
    )

    op.drop_index(
        "ix_movements_document_id",
        table_name="movements",
    )

    # Supprimer les tables
    op.drop_table("movements")
    op.drop_table("document_attachments")