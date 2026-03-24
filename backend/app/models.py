from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Funcionario(Base):
    """Pessoa física — identificada por nome + CPF parcial."""

    __tablename__ = "funcionarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    cpf_parcial: Mapped[str | None] = mapped_column(String(14))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), onupdate=_utcnow
    )

    cargos: Mapped[list["Cargo"]] = relationship(
        back_populates="funcionario", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("nome", "cpf_parcial", name="uq_funcionario_nome_cpf"),
    )

    def __repr__(self) -> str:
        return f"<Funcionario {self.nome} ({self.cpf_parcial})>"


class Cargo(Base):
    """Vínculo/cargo de um funcionário — cada matrícula é um cargo distinto."""

    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id", ondelete="CASCADE"), nullable=False
    )
    matricula: Mapped[str] = mapped_column(String(20), nullable=False)
    orgao: Mapped[str | None] = mapped_column(String(300))
    setor: Mapped[str | None] = mapped_column(String(300))
    cargo: Mapped[str | None] = mapped_column(String(200))
    cargo2: Mapped[str | None] = mapped_column(String(200))
    data_admissao: Mapped[date | None] = mapped_column(Date)
    vinculo: Mapped[str | None] = mapped_column(String(100))
    carga_horaria_semanal: Mapped[int | None] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), onupdate=_utcnow
    )

    funcionario: Mapped["Funcionario"] = relationship(back_populates="cargos")
    contracheques: Mapped[list["Contracheque"]] = relationship(
        back_populates="cargo_rel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("funcionario_id", "matricula", name="uq_cargo_func_matricula"),
    )

    def __repr__(self) -> str:
        return f"<Cargo {self.matricula} - {self.cargo}>"


class Contracheque(Base):
    """Registro mensal de contracheque — vinculado a um cargo específico."""

    __tablename__ = "contracheques"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cargo_id: Mapped[int] = mapped_column(
        ForeignKey("cargos.id", ondelete="CASCADE"), nullable=False
    )
    provento: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    desconto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    liquido: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    referencia_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia_ano: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    cargo_rel: Mapped["Cargo"] = relationship(back_populates="contracheques")

    __table_args__ = (
        UniqueConstraint(
            "cargo_id",
            "referencia_mes",
            "referencia_ano",
            name="uq_contracheque_cargo_ref",
        ),
    )

    def __repr__(self) -> str:
        return f"<Contracheque cargo_id={self.cargo_id} {self.referencia_mes}/{self.referencia_ano}>"


class SyncLog(Base):
    """Registro de execução de sync — só grava quando o sync completa com sucesso."""

    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    iniciado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finalizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    periodos_sincronizados: Mapped[int] = mapped_column(Integer, default=0)
    contracheques_novos: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<SyncLog {self.iniciado_em} sucesso={self.sucesso}>"
