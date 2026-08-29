"""create bureaux and assign bureau to users and documents

Revision ID: f1a7c9e2b4d6
Revises: d2f6c1a9e4b3
Create Date: 2026-08-28 23:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a7c9e2b4d6"
down_revision: Union[str, Sequence[str], None] = "d2f6c1a9e4b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # 1. Création de la table bureaux
    # ============================================================

    op.create_table(
        "bureaux",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "nom",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "actif",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("nom"),
    )

    op.create_index(
        "ix_bureaux_id",
        "bureaux",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_bureaux_code",
        "bureaux",
        ["code"],
        unique=False,
    )

    # ============================================================
    # 2. Création des quatre bureaux officiels
    # ============================================================

    op.execute(
        sa.text(
            """
            INSERT INTO bureaux (code, nom)
            VALUES
                ('CONTENTIEUX', 'Contentieux'),
                ('ENREGISTREMENT', 'Enregistrement'),
                ('DOMAINE_NOTARIAT', 'Domaine et notariat'),
                ('DOCUMENTATION_ARCHIVES', 'Documentation et archives')
            """
        )
    )

    # ============================================================
    # 3. Ajout de bureau_id dans users
    # ============================================================

    op.add_column(
        "users",
        sa.Column(
            "bureau_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_users_bureau_id",
        "users",
        ["bureau_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_users_bureau",
        "users",
        "bureaux",
        ["bureau_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # ============================================================
    # 4. Conversion des bureaux utilisateurs existants
    # ============================================================

    op.execute(
        sa.text(
            """
            UPDATE users
            SET bureau_id = (
                SELECT id
                FROM bureaux
                WHERE bureaux.code = 'ENREGISTREMENT'
            )
            WHERE bureau = 'ENREGISTREMENT'
            """
        )
    )

    # ADMIN : aucun bureau métier
    op.execute(
        sa.text(
            """
            UPDATE users
            SET bureau_id = NULL
            WHERE role = 'ADMIN'
            """
        )
    )

    # ============================================================
    # 5. Ajout de bureau_id dans documents
    # ============================================================

    op.add_column(
        "documents",
        sa.Column(
            "bureau_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_documents_bureau_id",
        "documents",
        ["bureau_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_documents_bureau",
        "documents",
        "bureaux",
        ["bureau_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # ============================================================
    # 6. Documents historiques
    # ============================================================
    #
    # Aucun bureau ne peut être déduit de manière fiable
    # des données actuellement disponibles.
    #
    # Ils restent donc volontairement NULL.
    #

    # ============================================================
    # 7. Suppression de l'ancien champ bureau texte
    # ============================================================

    op.drop_column(
        "users",
        "bureau",
    )


def downgrade() -> None:
    # ============================================================
    # 1. Restaurer l'ancien champ bureau texte
    # ============================================================

    op.add_column(
        "users",
        sa.Column(
            "bureau",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # ============================================================
    # 2. Restaurer les anciennes valeurs connues
    # ============================================================

    op.execute(
        sa.text(
            """
            UPDATE users
            SET bureau = 'ADMIN'
            WHERE role = 'ADMIN'
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET bureau = 'ENREGISTREMENT'
            WHERE role = 'USER'
              AND bureau_id = (
                  SELECT id
                  FROM bureaux
                  WHERE code = 'ENREGISTREMENT'
              )
            """
        )
    )

    # ============================================================
    # 3. Supprimer la relation documents -> bureaux
    # ============================================================

    op.drop_constraint(
        "fk_documents_bureau",
        "documents",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_documents_bureau_id",
        table_name="documents",
    )

    op.drop_column(
        "documents",
        "bureau_id",
    )

    # ============================================================
    # 4. Supprimer la relation users -> bureaux
    # ============================================================

    op.drop_constraint(
        "fk_users_bureau",
        "users",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_users_bureau_id",
        table_name="users",
    )

    op.drop_column(
        "users",
        "bureau_id",
    )

    # ============================================================
    # 5. Supprimer la table bureaux
    # ============================================================

    op.drop_index(
        "ix_bureaux_code",
        table_name="bureaux",
    )

    op.drop_index(
        "ix_bureaux_id",
        table_name="bureaux",
    )

    op.drop_table("bureaux")