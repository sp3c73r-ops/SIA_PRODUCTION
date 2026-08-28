"""merge document fields migration

Revision ID: 3abfbc257bf0
Revises: 9a0d272e706c, c1d9f2a7b6e8
Create Date: 2026-08-16 22:42:38.597130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3abfbc257bf0'
down_revision: Union[str, Sequence[str], None] = ('9a0d272e706c', 'c1d9f2a7b6e8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
