import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import ALLOWED_ORIGINS, BASE_DIR, DISCLAIMER, DATABASE_URL, USING_DEFAULT_SECRET
from .database import Base, SessionLocal, engine
from .routers import (auth_routes, cases, directory, documents, finance,
                      me, opinions, plan, trials)
from .seed import seed_if_empty

FRONTEND_DIST = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend", "dist"))


def _ensure_columns() -> None:
    """Tiny dev-friendly migration so existing local SQLite DBs gain new columns."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        def add(table: str, column: str, ddl: str) -> None:
            cols = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))

        add("case_packages", "share_token", "VARCHAR(64)")
        add("families", "consent_accepted", "BOOLEAN DEFAULT 0")
        add("families", "consent_at", "DATETIME")
        add("families", "country", "VARCHAR(10)")
        add("families", "plan_tier", "VARCHAR(20) DEFAULT 'free'")
        add("coverage_schemes", "category", "VARCHAR(30) DEFAULT 'general'")
        add("specialist_centers", "website", "VARCHAR(500)")
        add("cases", "country", "VARCHAR(10) DEFAULT 'IN'")
        add("specialist_centers", "country", "VARCHAR(10) DEFAULT 'IN'")
        add("coverage_schemes", "country", "VARCHAR(10) DEFAULT 'IN'")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Cancer Care Navigator API", version="0.2.0",
              description=DISCLAIMER, lifespan=lifespan)

if USING_DEFAULT_SECRET:
    import logging
    logging.getLogger("uvicorn.error").warning(
        "SECRET_KEY is not set — using development default. Set SECRET_KEY before real deployment.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth_routes.router, cases.router, documents.router,
               opinions.router, opinions.public_router, directory.router,
               trials.router, finance.router, me.router, plan.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}


from .legal_notes import (CROSS_BORDER_NOTES, REGION_LEGAL_NOTES,
                          cross_border_notes_for, notes_for_country)


@app.get("/api/legal/region-notes")
def legal_region_notes(country: str | None = None):
    """Per-country privacy-law summaries shown on the Privacy page."""
    if country:
        return notes_for_country(country)
    return {code: {"law": v["law"], "regulator": v["regulator"]}
            for code, v in REGION_LEGAL_NOTES.items()}


@app.get("/api/legal/international-access")
def international_access(country: str | None = None):
    """Cross-border participation: rules for getting treatment (or joining
    trials) in another country."""
    return {
        "for_your_country": cross_border_notes_for(country),
        "general": [n for n in CROSS_BORDER_NOTES if "ALL" in n["applies_to"]],
        "disclaimer": ("Visa and reimbursement rules change; confirm with the destination "
                       "hospital's international patient desk and your home insurer in writing."),
    }


@app.get("/api/legal/ropa")
def ropa():
    """Records of Processing Activities (GDPR Art. 30 style summary)."""
    return {
        "controller": "Your deployment operator (self-hosted) — fill organisation name before launch",
        "processing": [
            {"purpose": "Account & authentication", "data": ["email", "salted password hash", "consent timestamp"],
             "lawful_basis": "Consent (Art. 6(1)(a)/9(2)(a))", "retention": "Until account deletion",
             "recipients": "None"},
            {"purpose": "Case file, timeline & decision flags", "data": ["patient details you enter", "document extractions"],
             "lawful_basis": "Explicit consent", "retention": "Until deletion", "recipients": "None"},
            {"purpose": "Second-opinion packages & share links",
             "data": ["snapshot of case + records you chose to include"],
             "lawful_basis": "Explicit consent", "retention": "Until deletion; links revocable anytime",
             "recipients": "Anyone you send the tokenised link to"},
            {"purpose": "Crowdsourced wait times", "data": ["centre name", "reported days"],
             "lawful_basis": "Consent", "retention": "Deleted with account", "recipients": "Other users (aggregate)"},
            {"purpose": "Security auditing", "data": ["event type", "account id", "timestamp"],
             "lawful_basis": "Legitimate interest (Art. 32)", "retention": "90 days", "recipients": "None"},
        ],
        "processors": [{"role": "Hosting/database provider (Render/Neon or your own VPS)",
                        "note": "No other sub-processors. No analytics. No ads."}],
        "international_transfers": ("Choose an hosting region matching your users (EEA region for EU users) "
                                    "or rely on provider SCCs; see README deployment stages."),
    }


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
