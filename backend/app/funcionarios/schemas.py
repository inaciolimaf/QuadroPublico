from datetime import datetime

from pydantic import BaseModel


class FuncionarioOut(BaseModel):
    id: int
    nome: str
    cpf_parcial: str | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class FuncionarioDetail(FuncionarioOut):
    cargos: list["CargoOut"] = []


class PaginatedFuncionarios(BaseModel):
    items: list[FuncionarioOut]
    total: int


from app.cargos.schemas import CargoOut  # noqa: E402

FuncionarioDetail.model_rebuild()
