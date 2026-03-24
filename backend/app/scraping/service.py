import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from queue import Queue

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Cargo, Contracheque, Funcionario, SyncLog
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
    stmt = select(
        Contracheque.referencia_ano, Contracheque.referencia_mes
    ).distinct()
    return {(row[0], row[1]) for row in db.execute(stmt).all()}


def _aggregate_records(records: list[EmployeeRecord]) -> list[EmployeeRecord]:
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
    html = fetch_page(year, month)
    raw = parse_page(html)
    records = _aggregate_records(raw)
    print(f"[PARSE] {year}/{month:02d}: {len(raw)} linhas -> {len(records)} registros")
    return year, month, records


def _discover_available_periods() -> list[tuple[int, int]]:
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
    print(f"[DISCOVERY] Total de períodos: {len(all_periods)}")
    return all_periods


# ---------- Batch operations usando SQLAlchemy Core + pg dialect ----------

def _batch_ensure_funcionarios(
    db: Session,
    records: list[EmployeeRecord],
    cache: dict[tuple[str, str | None], int],
) -> None:
    """Garante funcionários no banco. 1 INSERT multi-row + 1 SELECT com ANY."""
    needed_keys: set[tuple[str, str | None]] = set()
    for r in records:
        key = (r.nome, r.cpf_parcial)
        if key not in cache:
            needed_keys.add(key)

    if not needed_keys:
        return

    # 1) Multi-row INSERT ... ON CONFLICT DO NOTHING (1 roundtrip)
    values = [{"nome": k[0], "cpf_parcial": k[1]} for k in needed_keys]
    stmt = pg_insert(Funcionario.__table__).values(values)
    stmt = stmt.on_conflict_do_nothing(constraint="uq_funcionario_nome_cpf")
    db.execute(stmt)

    # 2) SELECT com ANY para buscar IDs (1 roundtrip)
    names = list({k[0] for k in needed_keys})
    rows = db.execute(
        text("SELECT id, nome, cpf_parcial FROM funcionarios WHERE nome = ANY(:names)"),
        {"names": names},
    ).all()

    for row in rows:
        cache[(row[1], row[2])] = row[0]


def _batch_ensure_cargos(
    db: Session,
    records: list[EmployeeRecord],
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> None:
    """Garante cargos no banco. 1 UPSERT multi-row + 1 SELECT com ANY."""
    # Deduplica por (func_id, matricula)
    unique: dict[tuple[int, str], dict] = {}
    for r in records:
        func_id = func_cache[(r.nome, r.cpf_parcial)]
        key = (func_id, r.matricula)
        unique[key] = {
            "funcionario_id": func_id,
            "matricula": r.matricula,
            "orgao": r.orgao,
            "setor": r.setor,
            "cargo": r.cargo,
            "cargo2": r.cargo2,
            "data_admissao": r.data_admissao,
            "vinculo": r.vinculo,
            "carga_horaria_semanal": r.carga_horaria_semanal,
        }

    if not unique:
        return

    # 1) Multi-row UPSERT (1 roundtrip)
    values = list(unique.values())
    stmt = pg_insert(Cargo.__table__).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_cargo_func_matricula",
        set_={
            "orgao": stmt.excluded.orgao,
            "setor": stmt.excluded.setor,
            "cargo": stmt.excluded.cargo,
            "cargo2": stmt.excluded.cargo2,
            "data_admissao": text("COALESCE(EXCLUDED.data_admissao, cargos.data_admissao)"),
            "vinculo": text("COALESCE(EXCLUDED.vinculo, cargos.vinculo)"),
            "carga_horaria_semanal": text("COALESCE(EXCLUDED.carga_horaria_semanal, cargos.carga_horaria_semanal)"),
            "atualizado_em": text("NOW()"),
        },
    )
    db.execute(stmt)

    # 2) SELECT IDs que não estão no cache (1 roundtrip)
    missing_func_ids = list({fid for (fid, _) in unique if (fid, _) not in cargo_cache}
                           | {fid for (fid, mat) in unique if (fid, mat) not in cargo_cache})
    if missing_func_ids:
        rows = db.execute(
            text("SELECT id, funcionario_id, matricula FROM cargos WHERE funcionario_id = ANY(:ids)"),
            {"ids": list(set(missing_func_ids))},
        ).all()
        for row in rows:
            cargo_cache[(row[1], row[2])] = row[0]


def _save_period_bulk(
    db: Session,
    year: int,
    month: int,
    records: list[EmployeeRecord],
    func_id_cache: dict[tuple[str, str | None], int],
    cargo_id_cache: dict[tuple[int, str], int],
) -> tuple[int, int]:
    """Salva período inteiro em ~5 roundtrips ao banco."""
    if not records:
        return 0, 0

    # 1) Funcionários: 2 roundtrips max
    _batch_ensure_funcionarios(db, records, func_id_cache)

    # 2) Cargos: 2 roundtrips max
    _batch_ensure_cargos(db, records, func_id_cache, cargo_id_cache)

    # 3) Contracheques: 1 roundtrip (multi-row UPSERT)
    cc_values = []
    for r in records:
        func_id = func_id_cache[(r.nome, r.cpf_parcial)]
        cargo_id = cargo_id_cache[(func_id, r.matricula)]
        cc_values.append({
            "cargo_id": cargo_id,
            "provento": float(r.provento),
            "desconto": float(r.desconto),
            "liquido": float(r.liquido),
            "referencia_mes": month,
            "referencia_ano": year,
        })

    stmt = pg_insert(Contracheque.__table__).values(cc_values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_contracheque_cargo_ref",
        set_={
            "provento": stmt.excluded.provento,
            "desconto": stmt.excluded.desconto,
            "liquido": stmt.excluded.liquido,
        },
    )
    db.execute(stmt)

    db.commit()
    return len(records), len(cc_values)


def sync_all(db: Session) -> dict:
    """Pipeline produtor/consumidor + bulk upsert."""
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
    print(f"[SYNC] Faltando: {len(missing)}, refresh 13º: {len(refresh)}, total: {len(to_fetch)}")

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
    func_id_cache: dict[tuple[str, str | None], int] = {}
    cargo_id_cache: dict[tuple[int, str], int] = {}

    total_records = 0
    total_contracheques = 0
    synced_periods = 0
    errors = 0

    result_queue: Queue = Queue(maxsize=PREFETCH_BUFFER)

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
            func_id_cache.clear()
            cargo_id_cache.clear()
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

    print(f"[SYNC] Concluído! {total_contracheques} contracheques, {total_records} registros (erros: {errors})")
    return {
        "status": "synced",
        "total_periods": len(all_periods),
        "synced_periods": synced_periods,
        "total_records_processed": total_records,
        "new_contracheques": total_contracheques,
        "errors": errors,
    }
