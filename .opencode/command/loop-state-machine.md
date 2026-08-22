---
description: Hardens the doctor-response state machine: exhaustive transition tests, fixtures only, no production logic changes unless a test proves a bug (then report the diff).
agent: loop-build
---

# Goal: OpinionRequest state machine — exhaustive transition coverage

Work ONLY on `backend/tests/` plus, if a test proves a defect, a minimal fix in
`backend/app/routers/opinions.py` or `backend/app/services/sla.py`.

Scope rules:
- Synthetic fixtures only ("Patient A", "Doctor 1"). No real names/files/diagnoses.
- Do NOT touch record ingestion, extraction, eligibility/matching, seed facts,
  outreach content, or anything under `backend/storage/**`.
- If a needed change falls outside those two files → STOP and report as blocked.

Build these tests (pytest, reuse patterns from tests/test_auth_scoping.py):
1. Legal transitions: drafted→sent→acknowledged→opinion_received; sent→no_response;
   sent→declined; acknowledged→opinion_received. Assert status + timestamps set.
2. Illegal transitions must 400: respond while drafted; respond while declined;
   mark_sent on anything except drafted; acknowledge before sent.
3. SLA edge cases: past-deadline 'sent' flips to no_response on list/sla-check;
   acknowledged past deadline does NOT auto-flip; future deadline untouched.
4. Conflict detection: two received opinions with different modalities flag both;
   identical modality clears conflict; third opinion re-evaluates all rows.

Verification before declaring complete (run from backend/):
- `..\.venv\Scripts\python.exe -m pytest tests -q` passes with new tests
- `..\.venv\Scripts\python.exe smoke_test.py` still fully green
- `git diff --stat` shows only files inside backend/tests/** (plus at most
  opinions.py / sla.py if a proven bug was fixed)

Stop conditions:
- All verification passes → summarize evidence (test names, diff stat).
- Task would require touching off-limits modules → stop and report as blocker.
