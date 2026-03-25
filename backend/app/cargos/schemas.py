from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.contracheques.schemas import ContrachequeOut


class CargoCreate(BaseModel):
    matricula: str
    orgao: str | None = None
    setor: str | None = None
    cargo: str | None = None
    cargo2: str | None = None
    data_admissao: date | None = None
    vinculo: str | None = None
    carga_horaria_semanal: int | None = None


class CargoUpdate(BaseModel):
    orgao: str | None = None
    setor: str | None = None
    cargo: str | None = None
    cargo2: str | None = None
    data_admissao: date | None = None
    vinculo: str | None = None
    carga_horaria_semanal: int | None = None


class CargoOut(BaseModel):
    id: int
    funcionario_id: int
    matricula: str
    orgao: str | None
    setor: str | None
    cargo: str | None
    cargo2: str | None
    data_admissao: date | None
    vinculo: str | None
    carga_horaria_semanal: int | None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class CargoDetail(CargoOut):
    contracheques: list[ContrachequeOut] = []


from app.contracheques.schemas import ContrachequeOut  # noqa: E402

CargoDetail.model_rebuild()
