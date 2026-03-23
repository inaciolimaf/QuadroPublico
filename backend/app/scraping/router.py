from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.scraping.service import sync_all

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    print("[ROUTE] Iniciando sincronização...")
    result = sync_all(db)
    print(f"[ROUTE] Sincronização finalizada: {result}")
    return result
