# Cancer Care Navigator (India) — MVP Skeleton

A case-management, decision-sequencing, and access-brokering platform for Indian cancer
patients and families. **This is not a diagnostic AI tool.** It never generates treatment
recommendations. It organizes records, surfaces time-sensitive decision risks (sourced from
published guidelines), and helps families run parallel second opinions and see financial /
logistics options faster.

> **Persistent disclaimer shown on every page and every generated PDF:**
> *"This is not medical advice. It organizes your records and flags questions to raise with
> your treating oncologist."*

---

## Quick start

### Backend (FastAPI)

```powershell
cd backend
python -m venv ..\.venv            # once
..\.venv\Scripts\python -m pip install -r requirements.txt   # once
..\.venv\Scripts\python -m app.seed                          # optional; also auto-seeds on startup
..\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend (React + Vite + Tailwind)

```powershell
cd frontend
npm install        # once
npm run dev        # http://localhost:5173  (proxies /api -> :8000)
```

`npm run build` produces `frontend/dist/`.

### Tests

```powershell
# from backend/, with the venv active:
python smoke_test.py          # 32 end-to-end checks across all 8 features
python -m pytest tests -q     # authorization-scoping tests
```

---

## What's real vs. stubbed/placeholder

| Area | Status | Notes |
|---|---|---|
| Auth + per-family scoping | **Real** | Email/password (PBKDF2), JWT bearer tokens. Every case/document/package route re-checks ownership server-side (`owned_case`). Verified by tests. |
| Data models (all 14 tables) | **Real** | SQLAlchemy 2.x; SQLite locally, Postgres via `DATABASE_URL`. |
| Document upload & storage | **Real** | Files on local disk under `backend/storage/<family>/<case>/…`, S3-shaped keys — swap `services/storage.py` for S3 later. Never stored as DB blobs. |
| OCR / extraction | **STUB** | `services/extraction.py::extract_document()` returns deterministic mock data marked `"ocr_engine": "stub"`. Users can correct fields in the UI. Plug in a real OCR API key here. |
| Foreclosure rules engine | **Real engine, curated content needed** | Keyword heuristics in `services/rules_engine.py` evaluate against 8 seeded rules with real guideline citations (NCCN, ASCO/JCO, BSH, Mankin). A clinician must review both rule text and predicates. |
| Case packages | **Real, immutable** | Snapshots freeze case state at generation; no update route exists (verified by test). New info ⇒ new version. |
| PDF export | **Real** | reportlab one-pager: patient summary + timeline + open questions with citations + disclaimer. |
| Doctor directory | **PLACEHOLDER** | Role-level entries only ("[placeholder]"), clearly badged. No real individuals. Dispatch is deliberately manual ("mark as sent"). |
| SLA tracking | **Real** | On-page-load check moves overdue `sent` requests to `no_response`; deadline = sent_at + avg_response_time + 2 days. |
| Conflict detection | **Real** | Distinct `opinion_recommended_modality` values across received opinions flag conflicts in the comparison view. |
| Specialist centres | **Starter seed list** | Real, well-known centres (Tata Memorial, AIIMS IRCH, Adyar WIA, Basavatarakam, Apollo Proton, etc.) with publicly documented capabilities. Badged "verify before relying". |
| Wait-time reports | **Real (crowdsourced)** | Family-submitted; 90-day rolling average per centre. Indicative only. |
| Trial search | **STUB** | `services/trials.py::search_trials()` filters placeholder example records (`CTRI-EXAMPLE-…`). Replace with live CTRI / ClinicalTrials.gov API v2. |
| Coverage schemes | **Seeded public info** | PM-JAY and CGHS described at the level of general public information + generic state-scheme entry. Parameters change — verify on official portals. Matching is rules-based only; **no insurance APIs are called**. |
| Assistance programmes | **PLACEHOLDER** | Realistic examples, badged as unverified. |

Every seeded/placeholder row renders with an amber **"unverified / example data"** badge in the
UI so it can never be mistaken for verified content.

## Configuration

Environment variables (all optional):

- `DATABASE_URL` — default `sqlite:///backend/app.db`. For production set e.g.
  `postgresql+psycopg://user:pass@host/dbname` (install `psycopg[binary]`). SQLite is a
  **dev convenience swap-out**, not the production target.
- `SECRET_KEY` — JWT signing secret. **Set this outside development.**
- `STORAGE_DIR` — file storage root (default `backend/storage`).

## Architecture notes (for specialist handoff)

Each feature's *content* is separated from its *code*, so domain experts can replace seed
data without touching logic:

- **Clinician** → `app/seed_data.py::FORECLOSURE_RULES` (rule text/citations) +
  `app/services/rules_engine.py::RULE_PREDICATES` (match conditions).
- **Insurance analyst** → `app/seed_data.py::COVERAGE_SCHEMES` (structured
  `eligibility_criteria_json` with simple `in` / `not_in` / `in_or_unknown` checks) +
  `PAPs`.
- **Ops** → real doctor directory rows, centre verification dates, wait-time moderation.
- **Engineering** → OCR integration point: `services/extraction.py`; trial API integration
  point: `services/trials.py`; storage swap: `services/storage.py`.

## Deliberately NOT built

- No AI-generated treatment recommendations of any kind.
- No autonomous diagnosis from uploaded images/scans.
- No automated dispatch of opinion requests to doctors (manual "mark as sent" only).
- No real financial/insurance API integrations (seeded rules-based matching only).

## What a human must do next to move from skeleton → product

1. Curate and verify a real doctor directory (consent, contacts, response times).
2. Clinician review of all foreclosure rule text + trigger conditions.
3. Insurance-analyst verification of scheme parameters against current official sources.
4. Plug in a real OCR/extraction pipeline (API key) behind `extract_document()`.
5. Integrate live CTRI / ClinicalTrials.gov trial search.
6. Swap SQLite → PostgreSQL, set a strong `SECRET_KEY`, move storage to S3-compatible object store.
7. Add rate limiting, audit logging, and a privacy review before handling real patient records.
