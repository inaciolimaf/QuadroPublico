from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.cargos.repository import get_cargo
from app.contracheques import repository as repo
from app.contracheques.schemas import ContrachequeOut

router = APIRouter(
    prefix="/cargos/{cargo_id}/contracheques", tags=["contracheques"]
)


def _ensure_cargo(cargo_id: int, db: Session):
    if not get_cargo(db, cargo_id):
        raise HTTPException(status_code=404, detail="Cargo não encontrado")


@router.get("/", response_model=list[ContrachequeOut])
def list_contracheques(cargo_id: int, db: Session = Depends(get_db)):
    _ensure_cargo(cargo_id, db)
    return repo.list_contracheques(db, cargo_id)


@router.get("/{contracheque_id}", response_model=ContrachequeOut)
def get_contracheque(cargo_id: int, contracheque_id: int, db: Session = Depends(get_db)):
    _ensure_cargo(cargo_id, db)
    contracheque = repo.get_contracheque(db, contracheque_id)
    if not contracheque or contracheque.cargo_id != cargo_id:
        raise HTTPException(status_code=404, detail="Contracheque não encontrado")
    return contracheque
