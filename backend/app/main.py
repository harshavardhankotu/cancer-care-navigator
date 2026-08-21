import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import BASE_DIR, DISCLAIMER, DATABASE_URL
from .database import Base, SessionLocal, engine
from .routers import (auth_routes, cases, directory, documents, finance,
                      opinions, trials)
from .seed import seed_if_empty

FRONTEND_DIST = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend", "dist"))


def _ensure_columns() -> None:
    """Tiny dev-friendly migration so existing local SQLite DBs gain new columns."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(case_packages)"))}
        if "share_token" not in cols:
            conn.execute(text("ALTER TABLE case_packages ADD COLUMN share_token VARCHAR(64)"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Cancer Care Navigator API", version="0.2.0",
              description=DISCLAIMER, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth_routes.router, cases.router, documents.router,
               opinions.router, opinions.public_router, directory.router,
               trials.router, finance.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}


# ---- Single-process production serving ($0 hosting friendly) ----
# If frontend/dist exists, this ONE uvicorn process serves API + app.
if os.path.isdir(FRONTEND_DIST):
    if os.path.isdir(os.path.join(FRONTEND_DIST, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")),
                  name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        candidate = os.path.normpath(os.path.join(FRONTEND_DIST, full_path))
        if full_path and candidate.startswith(FRONTEND_DIST) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
