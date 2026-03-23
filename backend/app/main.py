import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.funcionarios.router import router as funcionarios_router
from app.cargos.router import router as cargos_router
from app.contracheques.router import router as contracheques_router
from app.scraping.router import router as scraping_router
from app.scraping.scheduler import start_auto_sync
from app.admin import setup_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_auto_sync()
    yield


app = FastAPI(title="QuadroPublico API", lifespan=lifespan)
setup_admin(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(funcionarios_router)
app.include_router(cargos_router)
app.include_router(contracheques_router)
app.include_router(scraping_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend estático em produção
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
