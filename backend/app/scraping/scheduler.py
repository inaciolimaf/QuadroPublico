import threading
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import Contracheque
from app.scraping.service import sync_all

SYNC_INTERVAL_HOURS = 24


def _needs_sync() -> bool:
    """Verifica se a última sync foi há mais de SYNC_INTERVAL_HOURS."""
    db = SessionLocal()
    try:
        stmt = select(func.max(Contracheque.criado_em))
        last_sync = db.scalar(stmt)
        if last_sync is None:
            print("[SCHEDULER] Banco vazio, sync necessário")
            return True
        # criado_em pode não ter timezone, normaliza
        if last_sync.tzinfo is None:
            last_sync = last_sync.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - last_sync
        hours = age.total_seconds() / 3600
        print(f"[SCHEDULER] Última sync há {hours:.1f}h (limite: {SYNC_INTERVAL_HOURS}h)")
        return age > timedelta(hours=SYNC_INTERVAL_HOURS)
    finally:
        db.close()


def _run_sync():
    """Executa sync em thread separada."""
    try:
        if not _needs_sync():
            print("[SCHEDULER] Sync não necessário, pulando")
            return
        print("[SCHEDULER] Iniciando sync automático...")
        db = SessionLocal()
        try:
            result = sync_all(db)
            print(f"[SCHEDULER] Sync automático concluído: {result}")
        finally:
            db.close()
    except Exception as e:
        print(f"[SCHEDULER] Erro no sync automático: {e}")


def start_auto_sync():
    """Dispara sync em background thread ao iniciar o server."""
    print("[SCHEDULER] Verificando necessidade de sync...")
    thread = threading.Thread(target=_run_sync, daemon=True)
    thread.start()
