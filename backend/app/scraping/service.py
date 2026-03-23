from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cargo, Contracheque, Funcionario

SPECIAL_MONTHS_THRESHOLD = 13  # 13º, adiantamento 13º, etc.
from app.scraping.fetcher import fetch_page
from app.scraping.parser import (
    EmployeeRecord,
    parse_available_months,
    parse_available_years,
    parse_page,
)

import os

MAX_WORKERS = 4 if os.getenv("ENV") == "production" else 12


def _get_or_create_funcionario(db: Session, nome: str, cpf_parcial: str | None) -> Funcionario:
    stmt = select(Funcionario).where(
        Funcionario.nome == nome,
        Funcionario.cpf_parcial == cpf_parcial,
    )
    func = db.scalars(stmt).first()
    if func:
        return func
    func = Funcionario(nome=nome, cpf_parcial=cpf_parcial)
    db.add(func)
    db.flush()
    return func


def _get_or_create_cargo(db: Session, funcionario: Funcionario, record: EmployeeRecord) -> Cargo:
    stmt = select(Cargo).where(
        Cargo.funcionario_id == funcionario.id,
        Cargo.matricula == record.matricula,
    )
    cargo = db.scalars(stmt).first()
    if cargo:
        # Atualiza campos que podem mudar
        cargo.orgao = record.orgao
        cargo.setor = record.setor
        cargo.cargo = record.cargo
        cargo.cargo2 = record.cargo2
        if record.data_admissao:
            cargo.data_admissao = record.data_admissao
        if record.vinculo:
            cargo.vinculo = record.vinculo
        if record.carga_horaria_semanal:
            cargo.carga_horaria_semanal = record.carga_horaria_semanal
        return cargo
    cargo = Cargo(
        funcionario_id=funcionario.id,
        matricula=record.matricula,
        orgao=record.orgao,
        setor=record.setor,
        cargo=record.cargo,
        cargo2=record.cargo2,
        data_admissao=record.data_admissao,
        vinculo=record.vinculo,
        carga_horaria_semanal=record.carga_horaria_semanal,
    )
    db.add(cargo)
    db.flush()
    return cargo


def _get_contracheque(db: Session, cargo_id: int, mes: int, ano: int) -> Contracheque | None:
    stmt = select(Contracheque).where(
        Contracheque.cargo_id == cargo_id,
        Contracheque.referencia_mes == mes,
        Contracheque.referencia_ano == ano,
    )
    return db.scalars(stmt).first()


def _get_existing_months(db: Session) -> set[tuple[int, int]]:
    """Retorna set de (ano, mes) que já tem pelo menos 1 contracheque."""
    stmt = select(
        Contracheque.referencia_ano, Contracheque.referencia_mes
    ).distinct()
    return {(row[0], row[1]) for row in db.execute(stmt).all()}


def _aggregate_records(records: list[EmployeeRecord]) -> list[EmployeeRecord]:
    """Agrupa registros por matrícula, somando provento/desconto/líquido.

    Um mesmo funcionário com a mesma matrícula pode aparecer várias vezes
    na mesma página (ex: salário base + gratificação). Matrículas diferentes
    são cargos diferentes e ficam separados.
    """
    grouped: dict[str, EmployeeRecord] = {}
    for r in records:
        if r.matricula in grouped:
            existing = grouped[r.matricula]
            existing.provento += r.provento
            existing.desconto += r.desconto
            existing.liquido += r.liquido
        else:
            # Copia para não mutar o original
            grouped[r.matricula] = EmployeeRecord(
                matricula=r.matricula,
                nome=r.nome,
                orgao=r.orgao,
                setor=r.setor,
                cargo=r.cargo,
                cargo2=r.cargo2,
                provento=r.provento,
                desconto=r.desconto,
                liquido=r.liquido,
                cpf_parcial=r.cpf_parcial,
                data_admissao=r.data_admissao,
                vinculo=r.vinculo,
                carga_horaria_semanal=r.carga_horaria_semanal,
            )
    return list(grouped.values())


def _fetch_and_parse(year: int, month: int) -> tuple[int, int, list[EmployeeRecord]]:
    """Busca e parseia uma página — roda em thread."""
    html = fetch_page(year, month)
    raw = parse_page(html)
    records = _aggregate_records(raw)
    print(f"[PARSE] {year}/{month:02d}: {len(raw)} linhas -> {len(records)} registros (após agregação)")
    return year, month, records


def _discover_available_periods() -> list[tuple[int, int]]:
    """Descobre todos os anos e meses disponíveis no portal."""
    print("[DISCOVERY] Buscando anos disponíveis...")
    html = fetch_page(2026, 1)
    years = parse_available_years(html)
    print(f"[DISCOVERY] Anos encontrados: {years}")

    all_periods: list[tuple[int, int]] = []

    # Busca meses de cada ano em paralelo
    def _fetch_months_for_year(year: int) -> list[tuple[int, int]]:
        html = fetch_page(year, 1)
        months = parse_available_months(html, year)
        print(f"[DISCOVERY] {year}: meses disponíveis = {months}")
        return [(year, m) for m in months]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_months_for_year, y): y for y in years}
        for future in as_completed(futures):
            all_periods.extend(future.result())

    all_periods.sort()
    print(f"[DISCOVERY] Total de períodos disponíveis: {len(all_periods)}")
    return all_periods


def sync_all(db: Session) -> dict:
    """Sincroniza todos os dados do portal com o banco."""
    existing = _get_existing_months(db)
    print(f"[SYNC] Meses já no banco: {len(existing)}")

    all_periods = _discover_available_periods()

    current_year = datetime.now(timezone.utc).year

    # Filtra períodos que faltam + meses especiais (>=13) do ano corrente sempre
    missing: list[tuple[int, int]] = []
    refresh: list[tuple[int, int]] = []
    for y, m in all_periods:
        if (y, m) not in existing:
            missing.append((y, m))
        elif m >= SPECIAL_MONTHS_THRESHOLD and y == current_year:
            refresh.append((y, m))

    to_fetch = missing + refresh
    print(f"[SYNC] Períodos faltando: {len(missing)}, refresh 13º ano corrente: {len(refresh)}, total a buscar: {len(to_fetch)}")

    if not to_fetch:
        print("[SYNC] Banco já está atualizado!")
        return {
            "status": "up_to_date",
            "total_periods": len(all_periods),
            "synced": 0,
        }

    # Processa 1 período por vez: baixa, parseia, salva, libera memória
    # Evita acumular dezenas de páginas de 4-8MB na memória
    func_cache: dict[tuple[str, str | None], Funcionario] = {}
    cargo_cache: dict[tuple[int, str], Cargo] = {}

    total_records = 0
    total_contracheques = 0
    synced_periods = 0
    for i, (year, month) in enumerate(sorted(to_fetch), 1):
        print(f"[SYNC] [{i}/{len(to_fetch)}] Processando {year}/{month:02d}...")
        try:
            html = fetch_page(year, month)
            raw = parse_page(html)
            records = _aggregate_records(raw)
            del html  # libera memória da página
            print(f"[SYNC] [{i}/{len(to_fetch)}] {year}/{month:02d}: {len(raw)} linhas -> {len(records)} registros")

            for record in records:
                func_key = (record.nome, record.cpf_parcial)
                if func_key not in func_cache:
                    func_cache[func_key] = _get_or_create_funcionario(db, record.nome, record.cpf_parcial)
                funcionario = func_cache[func_key]

                cargo_key = (funcionario.id, record.matricula)
                if cargo_key not in cargo_cache:
                    cargo_cache[cargo_key] = _get_or_create_cargo(db, funcionario, record)
                else:
                    _get_or_create_cargo(db, funcionario, record)
                cargo_obj = cargo_cache[cargo_key]

                existing_cc = _get_contracheque(db, cargo_obj.id, month, year)
                if existing_cc:
                    if (existing_cc.provento != record.provento
                            or existing_cc.desconto != record.desconto
                            or existing_cc.liquido != record.liquido):
                        existing_cc.provento = record.provento
                        existing_cc.desconto = record.desconto
                        existing_cc.liquido = record.liquido
                        total_contracheques += 1
                else:
                    contracheque = Contracheque(
                        cargo_id=cargo_obj.id,
                        provento=record.provento,
                        desconto=record.desconto,
                        liquido=record.liquido,
                        referencia_mes=month,
                        referencia_ano=year,
                    )
                    db.add(contracheque)
                    total_contracheques += 1

                total_records += 1

            db.commit()
            synced_periods += 1
            print(f"[SYNC] [{i}/{len(to_fetch)}] {year}/{month:02d} salvo!")

        except Exception as e:
            print(f"[SYNC] ERRO em {year}/{month:02d}: {e}")
            db.rollback()

    print(f"[SYNC] Concluído! {total_contracheques} contracheques novos de {total_records} registros processados")
    return {
        "status": "synced",
        "total_periods": len(all_periods),
        "synced_periods": synced_periods,
        "total_records_processed": total_records,
        "new_contracheques": total_contracheques,
    }
