import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from queue import Queue

from sqlalchemy import text, select
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


# ---------- Batch SQL ----------

def _batch_ensure_funcionarios(
    db: Session,
    records: list[EmployeeRecord],
    cache: dict[tuple[str, str | None], int],
) -> None:
    """Garante que todos os funcionários existem no banco e atualiza o cache.
    Faz no máximo 2 roundtrips: 1 batch INSERT + 1 batch SELECT."""
    # Identifica chaves que não estão no cache
    needed: dict[tuple[str, str | None], EmployeeRecord] = {}
    for r in records:
        key = (r.nome, r.cpf_parcial)
        if key not in cache:
            needed[key] = r

    if not needed:
        return

    # Batch INSERT ... ON CONFLICT DO NOTHING (1 roundtrip via executemany)
    insert_params = [{"nome": k[0], "cpf_parcial": k[1]} for k in needed]
    db.execute(
        text("""
            INSERT INTO funcionarios (nome, cpf_parcial)
            VALUES (:nome, :cpf_parcial)
            ON CONFLICT ON CONSTRAINT uq_funcionario_nome_cpf DO NOTHING
        """),
        insert_params,
    )

    # Batch SELECT para pegar os IDs (1 roundtrip)
    # Usa VALUES join com IS NOT DISTINCT FROM para tratar NULLs
    # Constrói query dinâmica com placeholders numerados
    values_clauses = []
    params = {}
    for i, (nome, cpf) in enumerate(needed):
        values_clauses.append(f"(:n{i}, :c{i})")
        params[f"n{i}"] = nome
        params[f"c{i}"] = cpf

    values_sql = ", ".join(values_clauses)
    rows = db.execute(
        text(f"""
            SELECT f.id, f.nome, f.cpf_parcial
            FROM funcionarios f
            JOIN (VALUES {values_sql}) AS v(nome, cpf_parcial)
              ON f.nome = v.nome
             AND f.cpf_parcial IS NOT DISTINCT FROM v.cpf_parcial
        """),
        params,
    ).all()

    for row in rows:
        cache[(row[1], row[2])] = row[0]


def _batch_ensure_cargos(
    db: Session,
    records: list[EmployeeRecord],
    func_cache: dict[tuple[str, str | None], int],
    cargo_cache: dict[tuple[int, str], int],
) -> None:
    """Garante que todos os cargos existem e estão atualizados.
    Faz 1 roundtrip via executemany (UPSERT com RETURNING)."""
    # Deduplica por (funcionario_id, matricula) — pega o último registro
    unique: dict[tuple[int, str], EmployeeRecord] = {}
    for r in records:
        func_id = func_cache[(r.nome, r.cpf_parcial)]
        unique[(func_id, r.matricula)] = r

    upsert_params = []
    for (func_id, matricula), r in unique.items():
        upsert_params.append({
            "funcionario_id": func_id,
            "matricula": matricula,
            "orgao": r.orgao,
            "setor": r.setor,
            "cargo": r.cargo,
            "cargo2": r.cargo2,
            "data_admissao": r.data_admissao,
            "vinculo": r.vinculo,
            "carga_horaria_semanal": r.carga_horaria_semanal,
        })

    if not upsert_params:
        return

    # executemany não retorna rows, então fazemos upsert + select separados
    db.execute(
        text("""
            INSERT INTO cargos (funcionario_id, matricula, orgao, setor, cargo, cargo2,
                                data_admissao, vinculo, carga_horaria_semanal)
            VALUES (:funcionario_id, :matricula, :orgao, :setor, :cargo, :cargo2,
                    :data_admissao, :vinculo, :carga_horaria_semanal)
            ON CONFLICT ON CONSTRAINT uq_cargo_func_matricula
            DO UPDATE SET orgao = EXCLUDED.orgao,
                          setor = EXCLUDED.setor,
                          cargo = EXCLUDED.cargo,
                          cargo2 = EXCLUDED.cargo2,
                          data_admissao = COALESCE(EXCLUDED.data_admissao, cargos.data_admissao),
                          vinculo = COALESCE(EXCLUDED.vinculo, cargos.vinculo),
                          carga_horaria_semanal = COALESCE(EXCLUDED.carga_horaria_semanal, cargos.carga_horaria_semanal),
                          atualizado_em = NOW()
        """),
        upsert_params,
    )

    # Busca IDs dos que não estão no cache
    missing = [(fid, mat) for (fid, mat) in unique if (fid, mat) not in cargo_cache]
    if not missing:
        return

    values_clauses = []
    params = {}
    for i, (fid, mat) in enumerate(missing):
        values_clauses.append(f"(CAST(:f{i} AS int), :m{i})")
        params[f"f{i}"] = fid
        params[f"m{i}"] = mat

    values_sql = ", ".join(values_clauses)
    rows = db.execute(
        text(f"""
            SELECT c.id, c.funcionario_id, c.matricula
            FROM cargos c
            JOIN (VALUES {values_sql}) AS v(funcionario_id, matricula)
              ON c.funcionario_id = v.funcionario_id
             AND c.matricula = v.matricula
        """),
        params,
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
    """Salva registros de um período com batch operations (~4 roundtrips)."""
    if not records:
        return 0, 0

    # 1) Batch ensure funcionários (max 2 roundtrips)
    _batch_ensure_funcionarios(db, records, func_id_cache)

    # 2) Batch ensure cargos (max 2 roundtrips)
    _batch_ensure_cargos(db, records, func_id_cache, cargo_id_cache)

    # 3) Batch upsert contracheques (1 roundtrip)
    cc_params = []
    for r in records:
        func_id = func_id_cache[(r.nome, r.cpf_parcial)]
        cargo_id = cargo_id_cache[(func_id, r.matricula)]
        cc_params.append({
            "cargo_id": cargo_id,
            "provento": float(r.provento),
            "desconto": float(r.desconto),
            "liquido": float(r.liquido),
            "referencia_mes": month,
            "referencia_ano": year,
        })

    db.execute(
        text("""
            INSERT INTO contracheques (cargo_id, provento, desconto, liquido, referencia_mes, referencia_ano)
            VALUES (:cargo_id, :provento, :desconto, :liquido, :referencia_mes, :referencia_ano)
            ON CONFLICT ON CONSTRAINT uq_contracheque_cargo_ref
            DO UPDATE SET provento = EXCLUDED.provento,
                          desconto = EXCLUDED.desconto,
                          liquido = EXCLUDED.liquido
            WHERE contracheques.provento != EXCLUDED.provento
               OR contracheques.desconto != EXCLUDED.desconto
               OR contracheques.liquido != EXCLUDED.liquido
        """),
        cc_params,
    )

    db.commit()
    return len(records), len(cc_params)


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
            # Limpa caches — IDs podem ser de transação que foi revertida
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
