import logging
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

logger = logging.getLogger(__name__)

SPECIAL_MONTHS_THRESHOLD = 13
MAX_WORKERS = 4 if os.getenv("ENV") == "production" else 12
PREFETCH_BUFFER = 2
BATCH_SIZE = 50


def _chunked(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


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
    return year, month, records


def _discover_available_periods() -> list[tuple[int, int]]:
    html = fetch_page(2026, 1)
    years = parse_available_years(html)
    all_periods: list[tuple[int, int]] = []

    def fetch_months(year: int) -> list[tuple[int, int]]:
        page_html = fetch_page(year, 1)
        months = parse_available_months(page_html, year)
        return [(year, m) for m in months]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_months, y): y for y in years}
        for future in as_completed(futures):
            all_periods.extend(future.result())

    all_periods.sort()
    return all_periods


def _preload_func_cache(db: Session) -> dict[tuple[str, str | None], int]:
    rows = db.execute(text("SELECT id, nome, cpf_parcial FROM funcionarios")).all()
    return {(row[1], row[2]): row[0] for row in rows}


def _preload_cargo_cache(db: Session) -> dict[tuple[int, str], int]:
    rows = db.execute(
        text("SELECT id, funcionario_id, matricula FROM cargos")
    ).all()
    return {(row[1], row[2]): row[0] for row in rows}


def _batch_insert_funcionarios(
    db: Session,
    records: list[EmployeeRecord],
    cache: dict[tuple[str, str | None], int],
) -> None:
    new_funcs: dict[tuple[str, str | None], dict] = {}
    for r in records:
        key = (r.nome, r.cpf_parcial)
        if key not in cache and key not in new_funcs:
            new_funcs[key] = {"nome": r.nome, "cpf_parcial": r.cpf_parcial}

    if not new_funcs:
        return

    values = list(new_funcs.values())
    for chunk in _chunked(values, BATCH_SIZE):
        db.execute(Funcionario.__table__.insert(), chunk)

    names = list({v["nome"] for v in values})
    rows = db.execute(
        text("SELECT id, nome, cpf_parcial FROM funcionarios WHERE nome = ANY(:names)"),
        {"names": names},
    ).all()
    for row in rows:
        cache[(row[1], row[2])] = row[0]


def _batch_upsert_cargos(
    db: Session,
    records: list[EmployeeRecord],
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> None:
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

    values = list(unique.values())
    for chunk in _chunked(values, BATCH_SIZE):
        stmt = pg_insert(Cargo.__table__).values(chunk)
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

    missing_func_ids = list({fid for (fid, mat) in unique if (fid, mat) not in cargo_cache})
    if missing_func_ids:
        rows = db.execute(
            text("SELECT id, funcionario_id, matricula FROM cargos WHERE funcionario_id = ANY(:ids)"),
            {"ids": missing_func_ids},
        ).all()
        for row in rows:
            cargo_cache[(row[1], row[2])] = row[0]


def _batch_upsert_contracheques(
    db: Session,
    year: int,
    month: int,
    records: list[EmployeeRecord],
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> int:
    cc_values = []
    for r in records:
        func_id = func_cache[(r.nome, r.cpf_parcial)]
        cargo_id = cargo_cache[(func_id, r.matricula)]
        cc_values.append({
            "cargo_id": cargo_id,
            "provento": float(r.provento),
            "desconto": float(r.desconto),
            "liquido": float(r.liquido),
            "referencia_mes": month,
            "referencia_ano": year,
        })

    for chunk in _chunked(cc_values, BATCH_SIZE):
        stmt = pg_insert(Contracheque.__table__).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_contracheque_cargo_ref",
            set_={
                "provento": stmt.excluded.provento,
                "desconto": stmt.excluded.desconto,
                "liquido": stmt.excluded.liquido,
            },
        )
        db.execute(stmt)

    return len(cc_values)


def _save_period(
    db: Session,
    year: int,
    month: int,
    records: list[EmployeeRecord],
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> tuple[int, int]:
    if not records:
        return 0, 0

    _batch_insert_funcionarios(db, records, func_cache)
    _batch_upsert_cargos(db, records, func_cache, cargo_cache)
    cc_count = _batch_upsert_contracheques(db, year, month, records, func_cache, cargo_cache)
    db.commit()
    return len(records), cc_count


def _classify_periods(
    all_periods: list[tuple[int, int]],
    existing: set[tuple[int, int]],
    current_year: int,
) -> list[tuple[int, int]]:
    missing = []
    refresh = []
    for y, m in all_periods:
        if (y, m) not in existing:
            missing.append((y, m))
        elif m >= SPECIAL_MONTHS_THRESHOLD and y == current_year:
            refresh.append((y, m))
    return sorted(missing + refresh)


def _create_sync_log(db: Session, inicio: datetime, **kwargs) -> SyncLog:
    log = SyncLog(iniciado_em=inicio, **kwargs)
    db.add(log)
    db.commit()
    return log


def _start_producer(to_fetch: list[tuple[int, int]], queue: Queue) -> threading.Thread:
    def produce():
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(_fetch_and_parse, y, m): (y, m)
                for y, m in to_fetch
            }
            for future in as_completed(futures):
                try:
                    queue.put(future.result())
                except Exception:
                    queue.put(None)
        queue.put("DONE")

    thread = threading.Thread(target=produce, daemon=True)
    thread.start()
    return thread


def _consume_results(
    db: Session,
    queue: Queue,
    total_to_process: int,
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> tuple[int, int, int, int]:
    total_records = 0
    total_contracheques = 0
    synced_periods = 0
    errors = 0

    while True:
        item = queue.get()
        if item == "DONE":
            break
        if item is None:
            errors += 1
            logger.warning("Falha ao baixar/parsear um período (item None)")
            continue

        year, month, records = item
        try:
            rec_count, cc_count = _save_period(
                db, year, month, records, func_cache, cargo_cache
            )
            total_records += rec_count
            total_contracheques += cc_count
            synced_periods += 1
            logger.info(
                "Período %d/%02d salvo (%d/%d): %d registros, %d contracheques",
                year, month, synced_periods, total_to_process, rec_count, cc_count,
            )
        except Exception:
            db.rollback()
            func_cache.clear()
            func_cache.update(_preload_func_cache(db))
            cargo_cache.clear()
            cargo_cache.update(_preload_cargo_cache(db))
            errors += 1
            logger.exception("Erro ao salvar período %d/%02d", year, month)

    return total_records, total_contracheques, synced_periods, errors


def sync_all(db: Session) -> dict:
    inicio = datetime.now(timezone.utc)
    logger.info("Sync iniciado")

    existing = _get_existing_months(db)
    all_periods = _discover_available_periods()
    current_year = datetime.now(timezone.utc).year

    to_fetch = _classify_periods(all_periods, existing, current_year)
    logger.info(
        "Descoberta concluída: %d períodos disponíveis, %d já no banco, %d para sincronizar",
        len(all_periods), len(existing), len(to_fetch),
    )

    if not to_fetch:
        _create_sync_log(db, inicio, sucesso=True, periodos_sincronizados=0, contracheques_novos=0)
        logger.info("Sync concluído: já atualizado, nada a fazer")
        return {"status": "up_to_date", "total_periods": len(all_periods), "synced": 0}

    func_cache = _preload_func_cache(db)
    cargo_cache = _preload_cargo_cache(db)

    queue: Queue = Queue(maxsize=PREFETCH_BUFFER)
    producer = _start_producer(to_fetch, queue)

    total_records, total_contracheques, synced_periods, errors = _consume_results(
        db, queue, len(to_fetch), func_cache, cargo_cache
    )

    producer.join()

    sucesso = errors == 0
    _create_sync_log(
        db,
        inicio,
        sucesso=sucesso,
        periodos_sincronizados=synced_periods,
        contracheques_novos=total_contracheques,
    )

    duracao = (datetime.now(timezone.utc) - inicio).total_seconds()
    logger.info(
        "Sync concluído (%s) em %.1fs: %d períodos, %d contracheques novos, %d erros",
        "sucesso" if sucesso else "com erros",
        duracao, synced_periods, total_contracheques, errors,
    )

    return {
        "status": "synced",
        "total_periods": len(all_periods),
        "synced_periods": synced_periods,
        "total_records_processed": total_records,
        "new_contracheques": total_contracheques,
        "errors": errors,
    }
