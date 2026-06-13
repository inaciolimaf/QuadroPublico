import logging
import threading
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import SyncLog
from app.scraping.service import sync_all

logger = logging.getLogger(__name__)

SYNC_INTERVAL_HOURS = 8


def _needs_sync() -> bool:
    db = SessionLocal()
    try:
        stmt = select(func.max(SyncLog.finalizado_em)).where(SyncLog.sucesso == True)
        last_success = db.scalar(stmt)
        if last_success is None:
            return True
        if last_success.tzinfo is None:
            last_success = last_success.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - last_success
        return age > timedelta(hours=SYNC_INTERVAL_HOURS)
    finally:
        db.close()


def _run_sync():
    try:
        if not _needs_sync():
            return
        db = SessionLocal()
        try:
            sync_all(db)
        finally:
            db.close()
    except (ConnectionError, OSError, RuntimeError) as e:
        logger.error("Erro no sync automático: %s", e)


def _sync_loop():
    while True:
        try:
            _run_sync()
        except Exception:  # noqa: BLE001 - o loop nunca pode morrer
            logger.exception("Erro inesperado no loop de sync automático")
        time.sleep(SYNC_INTERVAL_HOURS * 3600)


def start_auto_sync():
    thread = threading.Thread(target=_sync_loop, daemon=True)
    thread.start()
