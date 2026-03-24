"""add sync_logs table

Revision ID: b3f7a1d20e45
Revises: ac412e2c02a4
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3f7a1d20e45'
down_revision: Union[str, None] = 'ac412e2c02a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sucesso", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("periodos_sincronizados", sa.Integer, server_default="0"),
        sa.Column("contracheques_novos", sa.Integer, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("sync_logs")
