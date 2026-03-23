from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Funcionario


def _apply_search_filter(stmt, query: str | None):
    if query and query.strip():
        terms = query.strip().split()
        for term in terms:
            pattern = f"%{term}%"
            stmt = stmt.where(
                func.unaccent(Funcionario.nome).ilike(func.unaccent(pattern))
            )
    return stmt


def search_funcionarios(
    db: Session, query: str | None = None, skip: int = 0, limit: int = 50
) -> list[Funcionario]:
    stmt = select(Funcionario)
    stmt = _apply_search_filter(stmt, query)
    stmt = stmt.order_by(Funcionario.nome).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def count_funcionarios(db: Session, query: str | None = None) -> int:
    stmt = select(func.count()).select_from(Funcionario)
    stmt = _apply_search_filter(stmt, query)
    return db.scalar(stmt) or 0


def get_funcionario(db: Session, funcionario_id: int) -> Funcionario | None:
    stmt = (
        select(Funcionario)
        .where(Funcionario.id == funcionario_id)
        .options(selectinload(Funcionario.cargos))
    )
    return db.scalars(stmt).first()
