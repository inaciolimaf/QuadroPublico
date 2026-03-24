import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from queue import Queue

from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contracheque, SyncLog
from app.scraping.fetcher import fetch_page
from app.scraping.parser import (
    EmployeeRecord,
    parse_available_months,
    parse_available_years,
    parse_page,
)

SPECIAL_MONTHS_THRESHOLD = 13
MAX_WORKERS = 4 if os.getenv("ENV") == "production" else 12
PREFETCH_BUFFER = 3


def _get_existing_months(db: Session) -> set[tuple[int, int]]:
    """Retorna set de (ano, mes) que já tem pelo menos 1 contracheque."""
    stmt = select(
        Contracheque.referencia_ano, Contracheque.referencia_mes
    ).distinct()
    return {(row[0], row[1]) for row in db.execute(stmt).all()}


def _aggregate_records(records: list[EmployeeRecord]) -> list[EmployeeRecord]:
    """Agrupa registros por matrícula, somando provento/desconto/líquido."""
    grouped: dict[str, EmployeeRecord] = {}
    for r in records:
        if r.matricula in grouped:
            existing = grouped[r.matricula]
            existing.provento += r.provento
            existing.desconto += r.desconto
            existing.liquido += r.liquido
        else:
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


# ---------- Raw SQL lookups (sem ORM, sem session bloat) ----------

_SQL_FIND_FUNC = text("""
    SELECT id FROM funcionarios
    WHERE nome = :nome AND cpf_parcial IS NOT DISTINCT FROM :cpf_parcial
""")

_SQL_INSERT_FUNC = text("""
    INSERT INTO funcionarios (nome, cpf_parcial)
    VALUES (:nome, :cpf_parcial)
    RETURNING id
""")

_SQL_FIND_CARGO = text("""
    SELECT id FROM cargos
    WHERE funcionario_id = :funcionario_id AND matricula = :matricula
""")

_SQL_INSERT_CARGO = text("""
    INSERT INTO cargos (funcionario_id, matricula, orgao, setor, cargo, cargo2,
                        data_admissao, vinculo, carga_horaria_semanal)
    VALUES (:funcionario_id, :matricula, :orgao, :setor, :cargo, :cargo2,
            :data_admissao, :vinculo, :carga_horaria_semanal)
    RETURNING id
""")

_SQL_UPDATE_CARGO = text("""
    UPDATE cargos SET orgao = :orgao, setor = :setor, cargo = :cargo, cargo2 = :cargo2,
        data_admissao = COALESCE(:data_admissao, data_admissao),
        vinculo = COALESCE(:vinculo, vinculo),
        carga_horaria_semanal = COALESCE(:carga_horaria_semanal, carga_horaria_semanal),
        atualizado_em = NOW()
    WHERE id = :id
""")

_SQL_UPSERT_CONTRACHEQUES = text("""
    INSERT INTO contracheques (cargo_id, provento, desconto, liquido, referencia_mes, referencia_ano)
    VALUES (:cargo_id, :provento, :desconto, :liquido, :referencia_mes, :referencia_ano)
    ON CONFLICT ON CONSTRAINT uq_contracheque_cargo_ref
    DO UPDATE SET provento = EXCLUDED.provento,
                  desconto = EXCLUDED.desconto,
                  liquido = EXCLUDED.liquido
    WHERE contracheques.provento != EXCLUDED.provento
       OR contracheques.desconto != EXCLUDED.desconto
       OR contracheques.liquido != EXCLUDED.liquido
""")


def _resolve_func_id(
    db: Session,
    nome: str,
    cpf_parcial: str | None,
    cache: dict[tuple[str, str | None], int],
) -> int:
    """Retorna o ID do funcionário, criando se necessário. Usa cache."""
    key = (nome, cpf_parcial)
    if key in cache:
        return cache[key]
    row = db.execute(_SQL_FIND_FUNC, {"nome": nome, "cpf_parcial": cpf_parcial}).first()
    if row:
        cache[key] = row[0]
        return row[0]
    row = db.execute(_SQL_INSERT_FUNC, {"nome": nome, "cpf_parcial": cpf_parcial}).first()
    cache[key] = row[0]
    return row[0]


def _resolve_cargo_id(
    db: Session,
    func_id: int,
    record: EmployeeRecord,
    cache: dict[tuple[int, str], int],
) -> int:
    """Retorna o ID do cargo, criando/atualizando se necessário. Usa cache."""
    key = (func_id, record.matricula)
    params = {
        "orgao": record.orgao,
        "setor": record.setor,
        "cargo": record.cargo,
        "cargo2": record.cargo2,
        "data_admissao": record.data_admissao,
        "vinculo": record.vinculo,
        "carga_horaria_semanal": record.carga_horaria_semanal,
    }
    if key in cache:
        db.execute(_SQL_UPDATE_CARGO, {"id": cache[key], **params})
        return cache[key]
    row = db.execute(_SQL_FIND_CARGO, {"funcionario_id": func_id, "matricula": record.matricula}).first()
    if row:
        cache[key] = row[0]
        db.execute(_SQL_UPDATE_CARGO, {"id": row[0], **params})
        return row[0]
    row = db.execute(_SQL_INSERT_CARGO, {
        "funcionario_id": func_id,
        "matricula": record.matricula,
        **params,
    }).first()
    cache[key] = row[0]
    return row[0]


def _save_period_bulk(
    db: Session,
    year: int,
    month: int,
    records: list[EmployeeRecord],
    func_id_cache: dict[tuple[str, str | None], int],
    cargo_id_cache: dict[tuple[int, str], int],
) -> tuple[int, int]:
    """Salva registros de um período. Raw SQL + batch upsert de contracheques."""
    if not records:
        return 0, 0

    # 1) Resolve IDs de funcionários e cargos (com cache, raw SQL)
    cc_params = []
    for r in records:
        func_id = _resolve_func_id(db, r.nome, r.cpf_parcial, func_id_cache)
        _resolve_cargo_id(db, func_id, r, cargo_id_cache)
        cargo_id = cargo_id_cache[(func_id, r.matricula)]
        cc_params.append({
            "cargo_id": cargo_id,
            "provento": float(r.provento),
            "desconto": float(r.desconto),
            "liquido": float(r.liquido),
            "referencia_mes": month,
            "referencia_ano": year,
        })

    # 2) Batch upsert de contracheques (1 roundtrip executemany)
    if cc_params:
        db.execute(_SQL_UPSERT_CONTRACHEQUES, cc_params)

    db.commit()
    return len(records), len(cc_params)


def sync_all(db: Session) -> dict:
    """Sincroniza todos os dados do portal com o banco.

    Pipeline produtor/consumidor + bulk upsert.
    """
    inicio = datetime.now(timezone.utc)

    existing = _get_existing_months(db)
    print(f"[SYNC] Meses já no banco: {len(existing)}")

    all_periods = _discover_available_periods()

    current_year = datetime.now(timezone.utc).year

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
        log = SyncLog(
            iniciado_em=inicio,
            sucesso=True,
            periodos_sincronizados=0,
            contracheques_novos=0,
        )
        db.add(log)
        db.commit()
        return {
            "status": "up_to_date",
            "total_periods": len(all_periods),
            "synced": 0,
        }

    to_fetch_sorted = sorted(to_fetch)

    # Caches de IDs (não objetos ORM)
    func_id_cache: dict[tuple[str, str | None], int] = {}
    cargo_id_cache: dict[tuple[int, str], int] = {}

    total_records = 0
    total_contracheques = 0
    synced_periods = 0
    errors = 0

    result_queue: Queue[tuple[int, int, list[EmployeeRecord]] | None] = Queue(maxsize=PREFETCH_BUFFER)

    def _producer():
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(_fetch_and_parse, y, m): (y, m)
                for y, m in to_fetch_sorted
            }
            for future in as_completed(futures):
                y, m = futures[future]
                try:
                    result = future.result()
                    result_queue.put(result)
                except Exception as e:
                    print(f"[SYNC] ERRO ao buscar {y}/{m:02d}: {e}")
                    result_queue.put(None)
        result_queue.put("DONE")

    producer_thread = threading.Thread(target=_producer, daemon=True)
    producer_thread.start()

    processed = 0
    total_to_process = len(to_fetch_sorted)
    while True:
        item = result_queue.get()
        if item == "DONE":
            break
        if item is None:
            errors += 1
            processed += 1
            continue

        year, month, records = item
        processed += 1
        print(f"[SYNC] [{processed}/{total_to_process}] Salvando {year}/{month:02d} ({len(records)} registros)...")
        try:
            rec_count, cc_count = _save_period_bulk(
                db, year, month, records, func_id_cache, cargo_id_cache
            )
            total_records += rec_count
            total_contracheques += cc_count
            synced_periods += 1
            print(f"[SYNC] [{processed}/{total_to_process}] {year}/{month:02d} salvo!")
        except Exception as e:
            print(f"[SYNC] ERRO ao salvar {year}/{month:02d}: {e}")
            db.rollback()
            errors += 1

    producer_thread.join()

    sucesso = errors == 0
    log = SyncLog(
        iniciado_em=inicio,
        sucesso=sucesso,
        periodos_sincronizados=synced_periods,
        contracheques_novos=total_contracheques,
    )
    db.add(log)
    db.commit()

    print(f"[SYNC] Concluído! {total_contracheques} contracheques novos de {total_records} registros processados (erros: {errors})")
    return {
        "status": "synced",
        "total_periods": len(all_periods),
        "synced_periods": synced_periods,
        "total_records_processed": total_records,
        "new_contracheques": total_contracheques,
        "errors": errors,
    }
