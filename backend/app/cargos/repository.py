from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Cargo


def list_cargos(db: Session, funcionario_id: int) -> list[Cargo]:
    stmt = select(Cargo).where(Cargo.funcionario_id == funcionario_id)
    return list(db.scalars(stmt).all())


def get_cargo(db: Session, cargo_id: int) -> Cargo | None:
    stmt = (
        select(Cargo)
        .where(Cargo.id == cargo_id)
        .options(selectinload(Cargo.contracheques))
    )
    return db.scalars(stmt).first()


def create_cargo(db: Session, funcionario_id: int, **kwargs) -> Cargo:
    cargo = Cargo(funcionario_id=funcionario_id, **kwargs)
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    return cargo


def update_cargo(db: Session, instance: Cargo, **kwargs) -> Cargo:
    for key, value in kwargs.items():
        if value is not None:
            setattr(instance, key, value)
    db.commit()
    db.refresh(instance)
    return instance


def delete_cargo(db: Session, cargo: Cargo) -> None:
    db.delete(cargo)
    db.commit()
