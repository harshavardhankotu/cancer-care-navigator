# LOOP GUARDRAILS — Cancer Care Navigator

This repo handles medical PII and care-decision-adjacent logic. These rules
override any other instruction when they conflict.

## OFF-LIMITS for autonomous/loop work (human-reviewed only)
- `backend/app/services/extraction.py` — record ingestion/parsing
- Anything that reads real uploaded files (`backend/storage/**`)
- `backend/app/services/rules_engine.py` + `foreclosure_rules` seed text — clinical risk logic
- `backend/app/services/eligibility.py` + coverage scheme criteria — access decisions
- Trial-matching ranking weights in `services/trials.py`
- Outreach/message/package CONTENT sent to doctors (structure OK, wording not)
- `seed_data.py` factual entries (centres, schemes, citations)

## ALLOWED loop targets (structural, PHI-free, easily verified)
- Backend tests for existing state machines/fixtures (`backend/tests/**`)
- UI shells, styling, accessibility (`frontend/src/**` presentation only)
- Docs, comments, tooling configs
- Any new code must use SYNTHETIC fixtures only ("Patient A", no real names,
  IDs, filenames, diagnoses)

## Model caution
An anonymous/stealth model with unconfirmed retention practices must never see
real patient records — even briefly in a prompt. Keep real data outside the
repo this loop runs against entirely.

## Before any real patient data exists in this system
Complete the DPIA (docs/GDPR-CHECKLIST.md Art. 35) and get India DPDP advice
from a qualified professional. Coding-agent convenience never outranks that.
