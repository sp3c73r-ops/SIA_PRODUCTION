"""add bureau origine/destination to movements

Revision ID: e8b3f1a7c2d4
Revises: 6c2f4a8e1d90
Create Date: 2026-09-05

Evolution du workflow de transfert inter-bureaux.

Retrocompatibilite :
- les deux colonnes sont ajoutees NULLABLE ;
- bureau_origine_id est rempli (backfill) depuis documents.bureau_id
  pour les mouvements historiques ;
- bureau_destination_id reste NULL pour les mouvements historiques
  dont la destination est inconnue ;
- les NOUVEAUX mouvements doivent fournir une destination via le service.

Protection concurrence :
- index unique partiel PostgreSQL garantissant UN SEUL mouvement
  EN_COURS par document.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8b3f1a7c2d4"
down_revision: Union[str, Sequence[str], None] = "6c2f4a8e1d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --------------------------------------------------------
    # COLONNES (NULLABLE pour retrocompatibilite)
    # --------------------------------------------------------

    op.add_column(
        "movements",
        sa.Column(
            "bureau_origine_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "movements",
        sa.Column(
            "bureau_destination_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # --------------------------------------------------------
    # CLES ETRANGERES -> bureaux.id
    # --------------------------------------------------------

    op.create_foreign_key(
        "fk_movements_bureau_origine",
        "movements",
        "bureaux",
        ["bureau_origine_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_foreign_key(
        "fk_movements_bureau_destination",
        "movements",
        "bureaux",
        ["bureau_destination_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # --------------------------------------------------------
    # BACKFIL bureau_origine_id depuis documents.bureau_id
    # --------------------------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE movements m
            SET bureau_origine_id = d.bureau_id
            FROM documents d
            WHERE m.document_id = d.id
              AND m.bureau_origine_id IS NULL
            """
        )
    )

    # --------------------------------------------------------
    # INDEX
    # --------------------------------------------------------

    op.create_index(
        "ix_movements_bureau_origine_id",
        "movements",
        ["bureau_origine_id"],
        unique=False,
    )

    op.create_index(
        "ix_movements_bureau_destination_id",
        "movements",
        ["bureau_destination_id"],
        unique=False,
    )

    # Un seul mouvement EN_COURS par document (PostgreSQL).
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX ux_movements_document_en_cours
            ON movements (document_id)
            WHERE statut = 'EN_COURS'
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        sa.text(
            "DROP INDEX IF EXISTS ux_movements_document_en_cours"
        )
    )

    op.drop_index(
        "ix_movements_bureau_destination_id",
        table_name="movements",
    )

    op.drop_index(
        "ix_movements_bureau_origine_id",
        table_name="movements",
    )

    op.drop_constraint(
        "fk_movements_bureau_destination",
        "movements",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_movements_bureau_origine",
        "movements",
        type_="foreignkey",
    )

    op.drop_column(
        "movements",
        "bureau_destination_id",
    )

    op.drop_column(
        "movements",
        "bureau_origine_id",
    )
