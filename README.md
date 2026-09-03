# Cancer Care Navigator — MVP (global)

A case-management, decision-sequencing, and access-brokering platform for **cancer patients
and families worldwide**. **This is not a diagnostic AI tool.** It never generates treatment
recommendations. It organizes records, surfaces time-sensitive decision risks (sourced from
published guidelines), ranks centres on citable public facts, matches country coverage
schemes, prioritises in-country clinical trials, and helps families run parallel second
opinions faster.

**Now global:** 36+ seeded centres across 20+ countries, 17 public coverage schemes
(NHS, Medicaid/Medicare/ACA, SUS, GKV, ALD-100%, NHI caps, NHIS cancer co-pay support,
MediShield Life, PM-JAY & more), live worldwide trial search via ClinicalTrials.gov v2,
and a personalised **"My Plan"** per case: best local centres → schemes you may qualify
for → trials with sites in your country → questions to ask your oncologist → next steps.

> **Persistent disclaimer shown on every page and every generated PDF:**
> *"This is not medical advice. It organizes your records and flags questions to raise with
> your treating oncologist."*

---

## 💰 Core principle: 100% FREE of cost

Every layer runs on free, open-source, or keyless-public services. **No paid APIs, no paid tiers required.**

| Layer | What we use | Cost |
|---|---|---|
| Backend framework | FastAPI + SQLAlchemy | $0 |
| Database (dev / prod) | SQLite / [Neon](https://neon.tech) free Postgres | $0 |
| Hosting | [Render](https://render.com) free tier (Docker, one process serves app+API) | $0 |
| PDF generation | reportlab | $0 |
| Document extraction | pypdf text-layer reading (local) | $0 |
| Clinical trial search | ClinicalTrials.gov Data API v2 — public domain, no key | $0 |
| Auth | Self-hosted JWT + PBKDF2 | $0 |
| File storage | Local disk (S3-shaped swap point) | $0 |

Known trade-offs of the free tiers (documented, accepted): Render cold-starts after ~15 min
idle (~30–60 s wake-up); Neon compute pauses when idle; uploaded files on free deploys are
ephemeral unless you add a paid persistent disk — use the Neon DB as source of truth.

---

## 🚀 Deployment at scale — with complete control

| Stage | Setup | Cost | Control | Use when |
|---|---|---|---|---|
| 0 | Local dev (SQLite) | $0 | full | building |
| 1 | Render + Neon (`render.yaml`) | $0 | low (platform-managed) | first public users |
| **2** | **Single VPS: `docker compose up` + Caddy auto-HTTPS** | ~$4–6/mo (or your own hardware = $0) | **full — you own data, backups, uptime** | serious rollout |
| 3 | Split: managed Postgres + N app replicas + S3 storage | usage-based | high | large scale |

Stage 2 quick start:
```bash
cp .env.example .env   # fill DOMAIN, POSTGRES_PASSWORD, SECRET_KEY
docker compose up -d --build
./scripts/backup.sh    # add to cron nightly: 0 3 * * *
```
Caddy issues/renews TLS automatically. Scale path: point `DATABASE_URL` at managed Postgres,
raise app replicas behind the same Caddy, move `STORAGE_DIR` to object storage.

## 📱 App + browser

The frontend is an installable PWA: on Android/Chrome and iOS/Safari choose
“Add to Home Screen” — it runs full-screen like a native app, works offline for cached
pages, and always fetches fresh health data over the network (API responses are never cached).

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
python smoke_test.py          # 85 end-to-end checks across all features (83 passed offline + 2 live-registry skipped)
python -m pytest tests -q     # 24 authorization-scoping, state-machine & synthetic patient journey tests
```

How we test: `smoke_test.py` runs the full app **in a sandboxed in-process harness**
(fastapi TestClient) against a throwaway database — every run starts from scratch, so results
are deterministic and nothing touches real data. When offline, live trial registry checks
are gracefully skipped (83 passed / 85 checks total). `pytest` covers authorization scoping, the
opinion request state machine, and 9 end-to-end synthetic patient journeys on isolated temp DBs.
We also boot the real uvicorn server and probe endpoints over HTTP.

## 🔒 Security & privacy posture (audited)

Implemented controls:
- **Auth**: PBKDF2-hashed passwords, JWT bearer tokens; brute-force rate limiting on login
  (per IP+email, 429 after burst) and signup caps per network; common/short passwords rejected.
- **Authorization**: every case/document/package route re-verifies family ownership server-side
  (uniform 404s so records can't be probed); share links are token-gated and **revocable**.
- **Uploads**: type + size enforced *before* buffering (chunked read cap — no memory DoS);
  storage path traversal protection on all file operations.
- **Security headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  and `Referrer-Policy: strict-origin-when-cross-origin` middleware active.
- **CORS**: explicit origin allow-list via `ALLOWED_ORIGINS` env — no wildcard on health data.
- **Secrets**: startup warns loudly if `SECRET_KEY` is left as the dev default.
- **Privacy rights** (works for every feature): itemised notice, consent gate at registration,
  one-click export, complete self-service erasure including uploaded files and crowdsourced
  wait-time reports.
- **Audit trail**: security events (register, login failure, export, erasure, share link creation
  and revocation) logged under GDPR Art. 30/32 accountability principles with zero personal data.
- **Per-country law notes**: Privacy page renders the matching regime summary for 15+
  jurisdictions (DPDP, GDPR, UK GDPR, US state laws incl. WA My Health My Data, LGPD,
  PIPEDA, APPs, PDPA, APPI, PIPA, KVKK, POPIA, PIPL…).

Honest limits (fix before scale): in-memory rate limiting is per-process (add Redis with
multiple workers); tokens stay valid until expiry (72 h) with no server-side revocation list;
free-tier file storage is ephemeral; legal pages are templates needing qualified lawyer sign-off.

---

## 🚦 Staging & Pilot Readiness Status

- **Engineering Readiness: PASS** — 24 pytest unit/integration/journey tests pass, 85 smoke checks pass (83 in offline/sandboxed mode), zero-warning Vite frontend build (built in <1s).
- **Product Readiness: PASS** — Core journeys (new diagnosis, scattered records, 7-state second-opinion readiness lifecycle, transfer packing, financial matching, family access, date & trial transparency) are coherent, deterministic, and state-aware.
- **Clinical Readiness: REQUIRES QUALIFIED CLINICAL REVIEW** — Guideline foreclosure rules and clinical sequencing questions must be signed off by a licensed medical oncologist.
- **Legal/Privacy Readiness: REQUIRES QUALIFIED LEGAL REVIEW** — DPDP/GDPR templates, consent text, and cross-border notes require formal qualified legal and DPIA counsel review.
- **Directory Verification: REQUIRES HUMAN CURATION** — Specialist directory entries are placeholders requiring verified clinic coordinator contacts before public outreach.

> **Recommendation**: **Engineering-ready for controlled staging / human-reviewed pilot.** Production readiness must NOT be declared until human clinical and legal sign-offs are completed.

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
| — | **DPDP Act 2023 compliance layer**: explicit consent gate at registration (server-enforced), itemised privacy notice, Privacy + Terms pages, grievance-officer placeholder, children's-data confirmation | ✅ working |
| — | **Data-principal rights implemented**: one-click full data export (`GET /api/me/export`), complete erasure incl. uploaded files (`DELETE /api/me`) | ✅ working |

## Legal & compliance notes

Grounded in the **Digital Personal Data Protection Act, 2023** and DPDP Rules, 2025:

- **Consent** is free, specific, informed and given by clear affirmative action at signup;
  server rejects registration without it; withdrawal (account deletion) is as easy as giving it.
- **Itemised notice**: the Privacy page lists every data item collected with its exact purpose.
- **Rights**: access (export), correction (edit in app), erasure (self-service delete),
  grievance redressal, nomination — all described in plain language.
- **Children's data**: adding a minor requires the account holder to confirm they are a parent
  or lawful guardian (DPDP s.9).
- **Grievance Officer contact placeholder must be filled before launch** (required publication).
- The Privacy/Terms pages are templates — **get a lawyer's review before real patient use**.

### Hospital comparison & doctor policy (defamation-safe)

Hospitals are compared only on objective, publicly citable facts — ownership type,
NABH accreditation status, government scheme empanelment, capability breadth — each fact
carrying its source link and as-of date. Corporate ownership is recorded as a neutral
fact (it earns no score bonus). There are no user reviews anywhere in the platform, and
individual doctors are never scored or ranked. Patients get official self-check links:
[NABH directory](https://nabh.co/find-a-healthcare-organisation/),
[PM-JAY find-hospital](https://hospitals.pmjay.gov.in/Search/empnlWorkFlow.htm?actionFlag=ViewRegisteredHosptlsNew),
[state-wise PM-JAY de-empanelment list](https://snomedct.abdm.gov.in/hospital/de-empanelled)
(fraud/quality actions), [e-Daakhil consumer forum](https://edaakhil.nic.in/), and the
[NMC Indian Medical Register](https://www.nmc.org.in/information-desk/indian-medical-register/).

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
