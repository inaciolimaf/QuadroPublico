from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.funcionarios import repository as repo
from app.funcionarios.schemas import FuncionarioDetail, PaginatedFuncionarios

router = APIRouter(prefix="/funcionarios", tags=["funcionarios"])


@router.get("/", response_model=PaginatedFuncionarios)
def list_funcionarios(
    q: str | None = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    items = repo.search_funcionarios(db, query=q, skip=skip, limit=limit)
    total = repo.count_funcionarios(db, query=q)
    return {"items": items, "total": total}


@router.get("/{funcionario_id}", response_model=FuncionarioDetail)
def get_funcionario(funcionario_id: int, db: Session = Depends(get_db)):
    funcionario = repo.get_funcionario(db, funcionario_id)
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    return funcionario
