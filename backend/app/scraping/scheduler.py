import logging
import threading
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import SyncLog
from app.scraping.service import sync_all

logger = logging.getLogger(__name__)

SYNC_INTERVAL_HOURS = 24


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


def start_auto_sync():
    thread = threading.Thread(target=_run_sync, daemon=True)
    thread.start()
