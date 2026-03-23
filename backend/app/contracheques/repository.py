from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contracheque


def list_contracheques(db: Session, cargo_id: int) -> list[Contracheque]:
    stmt = (
        select(Contracheque)
        .where(Contracheque.cargo_id == cargo_id)
        .order_by(Contracheque.referencia_ano, Contracheque.referencia_mes)
    )
    return list(db.scalars(stmt).all())


def get_contracheque(db: Session, contracheque_id: int) -> Contracheque | None:
    return db.get(Contracheque, contracheque_id)


def create_contracheque(db: Session, cargo_id: int, **kwargs) -> Contracheque:
    contracheque = Contracheque(cargo_id=cargo_id, **kwargs)
    db.add(contracheque)
    db.commit()
    db.refresh(contracheque)
    return contracheque


def update_contracheque(db: Session, contracheque: Contracheque, **kwargs) -> Contracheque:
    for key, value in kwargs.items():
        if value is not None:
            setattr(contracheque, key, value)
    db.commit()
    db.refresh(contracheque)
    return contracheque


def delete_contracheque(db: Session, contracheque: Contracheque) -> None:
    db.delete(contracheque)
    db.commit()
