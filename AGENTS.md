# Project guidance — READ FIRST

## Working style (user requirement)
- **SPEED IS THE PRIORITY.** Build in large single passes; avoid many small confirm-round-trips.
- Batch related edits together → verify ONCE at the end (smoke + pytest + build) → commit & push immediately.
- Don't re-explain finished work; report outcomes tersely.

## Environment (verified working)
- Python venv: `.venv\` at project root — use `..\.venv\Scripts\python.exe` from `backend/`
- GitHub CLI installed AND authenticated (account: harshavardhankotu):
  `& "C:\Program Files\GitHub CLI\gh.exe" ...`
- Remote: https://github.com/harshavardhankotu/cancer-care-navigator (main). Push after every verified change.
- Reset dev DB before smoke runs: delete `backend/app.db` + `backend/storage/`

## Verify (from backend/, venv active)
```
python smoke_test.py        # ~85 end-to-end checks, sandboxed fresh DB each run
python -m pytest tests -q   # auth-scoping tests
cd ../frontend && npm run build
```

## Non-negotiables (never violate)
1. 100% free of cost — no paid APIs/tiers anywhere.
2. Persistent disclaimer on every screen/PDF; amber badges on all unverified data.
3. Never fabricate real doctor contacts/rankings; centres = official sites only.
4. Server-side family scoping on every data route; audit security-relevant events.
5. No AI treatment recommendations / diagnosis / auto-dispatch — information brokering only.
