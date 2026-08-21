# Cancer Care Navigator (India) — MVP

A case-management, decision-sequencing, and access-brokering platform for Indian cancer
patients and families. **This is not a diagnostic AI tool.** It never generates treatment
recommendations. It organizes records, surfaces time-sensitive decision risks (sourced from
published guidelines), and helps families run parallel second opinions and see financial /
logistics options faster.

> **Persistent disclaimer shown on every page and every generated PDF:**
> *"This is not medical advice. It organizes your records and flags questions to raise with
> your treating oncologist."*

---

## 💰 Core principle: 100% FREE of cost

Every layer of this project runs on free, open-source, or keyless-public services. **No paid
APIs, no paid tiers required, ever.**

| Layer | What we use | Cost |
|---|---|---|
| Backend framework | FastAPI + SQLAlchemy (open source) | ₹0 / $0 |
| Database (dev) | SQLite file | $0 |
| Database (prod) | [Neon](https://neon.tech) free tier — 3 GiB Postgres, scales to zero | $0 |
| Hosting (prod) | [Render](https://render.com) free tier — 750 hrs/mo, Docker | $0 |
| Frontend hosting (alt) | Vercel/Netlify hobby tier | $0 |
| PDF generation | reportlab (open source) | $0 |
| Document text extraction | pypdf reads digital-PDF text layers locally | $0 |
| OCR for scanned files | Manual correction UI (cloud OCR is a later swap-in point) | $0 |
| Clinical trial search | **ClinicalTrials.gov Data API v2 — public domain, NO API key** ([docs](https://clinicaltrials.gov/data-api/api)) | $0 |
| Auth | Self-hosted JWT + PBKDF2 (no auth SaaS) | $0 |
| File storage | Local disk / Render volume-shaped dir (S3 swap point kept) | $0 |

Known trade-offs of the free tiers (documented, accepted): Render cold-starts after ~15 min
idle (~30–60 s wake-up); Neon compute pauses when idle; uploaded files on free deploys are
ephemeral unless you add a paid persistent disk — use the Neon DB as source of truth.

---

## Quick start (local)

### One command (after first-time setup)

```powershell
# terminal 1 — backend (also serves the built frontend if frontend/dist exists)
cd backend; ..\.venv\Scripts\python -m uvicorn app.main:app --port 8000
# terminal 2 — frontend dev server with hot reload
cd frontend; npm run dev     # http://localhost:5173
```

First time only: create venv + install (`pip install -r backend/requirements.txt`),
`npm install` in `frontend/`.

### Try it instantly

Open http://localhost:5173 → click **“Try demo”** → explore a fully populated sample case
(`demo@navigator.app` / `demo1234`). No signup needed.

No-account tools: **Quick coverage check** and **Centres directory** work without login.

### Tests

```powershell
cd backend
python smoke_test.py          # 42 end-to-end checks across all features
python -m pytest tests -q     # authorization-scoping tests
```

---

## Feature status (verified by automated tests)

| # | Feature | Status |
|---|---|---|
| 1a | Case creation per family account | ✅ working |
| 1b | Document upload → free local extraction (digital PDFs auto-read) | ✅ working |
| 1c | Add record WITHOUT a file (manual timeline entry) | ✅ working |
| 1d | Chronological timeline grouped by date, source + type shown | ✅ working |
| 2 | Foreclosure rules engine — 8 real cited guideline flags (NCCN/ASCO/BSH/Mankin) | ✅ working |
| 2b | Acknowledge flags + re-check button | ✅ working |
| 3 | Case package snapshots — immutable, versioned, no update route (test-asserted) | ✅ working |
| 3b | PDF export (patient summary + timeline + open questions + disclaimer) | ✅ working |
| 3c | **Public share link** — doctor opens read-only snapshot/PDF, no account needed | ✅ working |
| 4 | Centre directory filterable by cancer type/capability (starter seed list) | ✅ working |
| 4b | Crowdsourced wait times, 90-day rolling average | ✅ working |
| 5 | Doctor outreach state machine: drafted→sent→acknowledged/received/no_response/declined | ✅ working |
| 5b | SLA check (on-load), overdue flagged | ✅ working |
| 5c | Side-by-side opinion comparison + modality conflict detection | ✅ working |
| 6 | Transfer-request checklist requested→received→uploaded | ✅ working |
| 7 | Trial search — **LIVE ClinicalTrials.gov v2** (+ India-site count), offline fallback to clearly-marked examples | ✅ working |
| 8 | Financial profile + PM-JAY/CGHS/state-scheme eligibility matching | ✅ working |
| 8b | Network-hospital match vs case hospitals; coverage-gap flags | ✅ working |
| 8c | Public “quick coverage check” page (lead-in flow, no login/case) | ✅ working |
| — | Per-family authorization scoping (server-side, test-covered) | ✅ working |
| — | Disclaimer bar on every screen + every PDF | ✅ working |
| — | Placeholder/unverified data badged amber everywhere | ✅ working |
| — | Single-process deploy (API + app in one uvicorn), SPA deep-link fallback | ✅ working |
| — | Demo account seeding | ✅ working |

Known limitations (honest list): CTRI has **no public API** so Indian-registry trials appear
only as clearly-marked example rows pending an official interface; scanned-image OCR needs a
future cloud API (swap point ready); doctor directory is role-level placeholders requiring
human curation; free-tier file storage is ephemeral on redeploy.

---

## Pain points found in review & how they were fixed (v0.2)

| Pain point | Fix shipped |
|---|---|
| Trials tab showed only fake data | Real, keyless ClinicalTrials.gov v2 integration + honest live/example badges |
| OCR stub polluted timelines with junk needing full manual correction | pypdf auto-reads digital PDFs (dates/type/source/findings); stub only for scans; one-click field correction; mode badge on every entry |
| No way to build a timeline without uploading a file | “Add record without file” — fastest path for paper-era records |
| Doctors couldn't receive a package without accounts/email infra | Tokenized public share link + WhatsApp-native Web Share button + public PDF |
| Two servers / complicated hosting blocked $0 deployment | FastAPI serves built frontend; Dockerfile + render.yaml; deep links work |
| Nothing to evaluate without signing up and entering data | Seeded demo family + “Try demo” button; public tools linked from login |
| Old local DBs would break on new columns | Tiny startup migration adds missing columns automatically |

---

## Deploy FREE ($0/month)

### Option A — single service (simplest)

1. Push this repo to GitHub (below).
2. [neon.tech](https://neon.tech) → create free project → copy connection string.
3. [render.com](https://render.com) → New → Blueprint → select your repo (uses `render.yaml`)
   → paste the Neon URL into `DATABASE_URL` → Deploy.
4. Done: `https://<app>.onrender.com` serves API **and** the React app. Cold starts after
   idle are normal on the free plan.

### Option B — split (nicer URLs)

Frontend → Vercel hobby (root=`frontend`, env `VITE_API_URL` not needed since `/api` proxy
is dev-only; set CORS already open). Backend+DB same as Option A.

---

## Push to YOUR GitHub (new project)

The repo is already git-initialized and committed locally. To put it on GitHub:

**With GitHub CLI (recommended):**
```powershell
winget install GitHub.cli
gh auth login
cd "path\to\cancer-care-navigator"
gh repo create cancer-care-navigator --public --source=. --push
```

**Without CLI:** create an empty repo at https://github.com/new (name:
`cancer-care-navigator`, do NOT initialize with README), then:
```powershell
cd "path\to\cancer-care-navigator"
git remote add origin https://github.com/<your-username>/cancer-care-navigator.git
git branch -M main
git push -u origin main
```

---

## Architecture notes (specialist handoff)

Content is separated from code so domain experts can replace seed data without touching logic:

- **Clinician** → `backend/app/seed_data.py::FORECLOSURE_RULES` +
  `services/rules_engine.py::RULE_PREDICATES`
- **Insurance analyst** → `seed_data.py::COVERAGE_SCHEMES` (structured checks:
  `in` / `not_in` / `in_or_unknown`) + PAPs
- **Ops** → real doctor directory rows, centre verification dates
- **Engineering swap points** → `services/extraction.py` (OCR),
  `services/trials.py` (CTRI integration), `services/storage.py` (S3)

## Deliberately NOT built

No AI-generated treatment recommendations · no autonomous diagnosis · no automated doctor
dispatch (manual “mark as sent” only) · no insurance APIs (rules-based matching only).

## Roadmap next

Hindi/Telugu/Tamil i18n · community moderation for wait times · CTRI ingestion when an
official interface exists · optional cloud OCR key slot · vernacular voice notes for record
entry.
