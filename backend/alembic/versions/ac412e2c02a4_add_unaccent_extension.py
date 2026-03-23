"""add unaccent extension

Revision ID: ac412e2c02a4
Revises: e1a5c7b60371
Create Date: 2026-03-23 18:17:11.813989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac412e2c02a4'
down_revision: Union[str, None] = 'e1a5c7b60371'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
