from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.cargos import repository as repo
from app.cargos.schemas import CargoDetail, CargoOut
from app.funcionarios.repository import get_funcionario

router = APIRouter(prefix="/funcionarios/{funcionario_id}/cargos", tags=["cargos"])


def _ensure_funcionario(funcionario_id: int, db: Session):
    if not get_funcionario(db, funcionario_id):
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")


@router.get("/", response_model=list[CargoOut])
def list_cargos(funcionario_id: int, db: Session = Depends(get_db)):
    _ensure_funcionario(funcionario_id, db)
    return repo.list_cargos(db, funcionario_id)


@router.get("/{cargo_id}", response_model=CargoDetail)
def get_cargo(funcionario_id: int, cargo_id: int, db: Session = Depends(get_db)):
    _ensure_funcionario(funcionario_id, db)
    cargo = repo.get_cargo(db, cargo_id)
    if not cargo or cargo.funcionario_id != funcionario_id:
        raise HTTPException(status_code=404, detail="Cargo não encontrado")
    return cargo
