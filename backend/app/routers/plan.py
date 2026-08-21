"""Personalised guidance engine — 'My Plan'.

Composes, for ONE case:
  1. Best-matching centres: patient's own country first (fact-scored), then
     global leaders worth travelling for.
  2. Coverage schemes for their country with eligibility status vs their
     financial profile.
  3. Recruiting clinical trials with sites in their country first.
  4. Questions to raise with the treating oncologist (from unacknowledged
     guideline flags).
  5. Simple next-steps checklist.

Everything is information-brokering over citable public data — no medical advice,
no automated decisions.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..database import get_db
from ..models import (CaseFinancialProfile, CoverageScheme, DecisionFlag,
                      Family, SpecialistCenter)
from ..routers.directory import _score_center
from ..services.eligibility import PROFILE_FIELDS, evaluate_scheme
from ..services.trials import search_trials

router = APIRouter(prefix="/api/cases", tags=["personal-plan"])


@router.get("/{case_id}/personal-plan")
def personal_plan(case_id: int, db: Session = Depends(get_db),
                  family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    country = ((case.country or family.country or "IN") or "IN").upper()

    # ---- 1. Centres: local first, then global ----
    scored = []
    for c in db.query(SpecialistCenter).all():
        notes = []
        for n in c.notes:
            notes.append(n)
        item = {
            "id": c.id, "name": c.name, "location": c.location, "country": c.country,
            "capabilities": c.capabilities or [],
            "score": _score_center(c, notes)["total"],
            "max_score": 14,
        }
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], (x["name"] or "").lower()))
    local = [c for c in scored if (c["country"] or "").upper() == country][:6]
    intl = [c for c in scored if (c["country"] or "").upper() != country][:6]

    # ---- 2. Schemes for this country vs financial profile ----
    prof_row = db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()
    profile = {f: getattr(prof_row, f) for f in PROFILE_FIELDS} if prof_row else {}
    schemes = (db.query(CoverageScheme)
               .filter(CoverageScheme.country == country).all())
    scheme_results = sorted(
        (evaluate_scheme(s, profile) for s in schemes),
        key=lambda r: {"eligible": 0, "needs_verification": 1, "not_eligible": 2}[r["status"]],
    )

    # ---- 3. Trials near them ----
    try:
        trials = search_trials(db, case.cancer_type, None, include_live=True,
                               country=country)["results"][:5]
    except Exception:
        trials = []

    # ---- 4. Questions from open flags ----
    flags = (db.query(DecisionFlag)
             .filter(DecisionFlag.case_id == case.id,
                     DecisionFlag.acknowledged.is_(False)).all())
    questions = []
    for f in flags:
        if f.flag_type == "foreclosure" and f.rule:
            questions.append({
                "question": f"Should we confirm {f.rule.condition_description.split('(')[0].strip().rstrip('.').lower()} before proceeding?",
                "why_it_matters": f.rule.foreclosed_option,
                "source": f"{f.rule.source_guideline} — {f.rule.source_citation}",
            })
        elif f.message:
            questions.append({"question": f.message.split("\n")[0],
                              "why_it_matters": None, "source": None})

    plan = {
        "country": country,
        "local_centres": local,
        "global_centres": intl,
        "schemes": [{"scheme_name": s.scheme_name, "coverage_limit": s.coverage_limit,
                     "summary": (s.eligibility_criteria_json or {}).get("summary"),
                     **evaluate_scheme(s, profile)} for s in schemes],
        "scheme_results": scheme_results,
        "trials": trials,
        "questions_to_ask": questions,
        "next_steps": [
            f"Shortlist 1–2 centres above and ask your current hospital for records transfer",
            "Send your case package (Second Opinions tab) to 2–3 doctors in parallel",
            "Verify scheme eligibility at the official portal — links are on each scheme card",
            "Check recruiting trials with your oncologist — participation is always voluntary",
        ],
        "disclaimer": ("This plan organises public information around YOUR case. It is not "
                       "medical advice; decisions rest with you and your treating doctors."),
    }
    return plan
