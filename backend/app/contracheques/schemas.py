from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ContrachequeCreate(BaseModel):
    provento: Decimal
    desconto: Decimal = Decimal("0")
    liquido: Decimal
    referencia_mes: int
    referencia_ano: int


class ContrachequeUpdate(BaseModel):
    provento: Decimal | None = None
    desconto: Decimal | None = None
    liquido: Decimal | None = None


class ContrachequeOut(BaseModel):
    id: int
    cargo_id: int
    provento: Decimal
    desconto: Decimal
    liquido: Decimal
    referencia_mes: int
    referencia_ano: int
    criado_em: datetime

    model_config = {"from_attributes": True}
