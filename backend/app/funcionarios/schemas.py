from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.cargos.schemas import CargoOut


class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf_parcial: str | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class FuncionarioDetail(FuncionarioOut):
    cargos: list[CargoOut] = []


class PaginatedFuncionarios(BaseModel):
    items: list[FuncionarioOut]
    total: int


from app.cargos.schemas import CargoOut  # noqa: E402

FuncionarioDetail.model_rebuild()
