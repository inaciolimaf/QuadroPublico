"""create funcionarios, cargos and contracheques

Revision ID: e1a5c7b60371
Revises:
Create Date: 2026-03-23 17:38:45.393203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a5c7b60371'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "funcionarios",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(300), nullable=False, index=True),
        sa.Column("cpf_parcial", sa.String(14)),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("nome", "cpf_parcial", name="uq_funcionario_nome_cpf"),
    )

    op.create_table(
        "cargos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "funcionario_id",
            sa.Integer,
            sa.ForeignKey("funcionarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("matricula", sa.String(20), nullable=False),
        sa.Column("orgao", sa.String(300)),
        sa.Column("setor", sa.String(300)),
        sa.Column("cargo", sa.String(200)),
        sa.Column("cargo2", sa.String(200)),
        sa.Column("data_admissao", sa.Date),
        sa.Column("vinculo", sa.String(100)),
        sa.Column("carga_horaria_semanal", sa.Integer),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("funcionario_id", "matricula", name="uq_cargo_func_matricula"),
    )

    op.create_table(
        "contracheques",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "cargo_id",
            sa.Integer,
            sa.ForeignKey("cargos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provento", sa.Numeric(12, 2), nullable=False),
        sa.Column("desconto", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("liquido", sa.Numeric(12, 2), nullable=False),
        sa.Column("referencia_mes", sa.Integer, nullable=False),
        sa.Column("referencia_ano", sa.Integer, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "cargo_id",
            "referencia_mes",
            "referencia_ano",
            name="uq_contracheque_cargo_ref",
        ),
    )


def downgrade() -> None:
    op.drop_table("contracheques")
    op.drop_table("cargos")
    op.drop_table("funcionarios")
