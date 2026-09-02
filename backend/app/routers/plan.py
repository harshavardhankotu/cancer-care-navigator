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
from ..legal_notes import cross_border_notes_for
from ..models import (CaseFinancialProfile, CoverageScheme, DecisionFlag,
                      Family, SpecialistCenter)
from ..routers.directory import _score_center
from ..services.eligibility import PROFILE_FIELDS, evaluate_scheme
from ..services.trials import search_trials

router = APIRouter(prefix="/api/cases", tags=["personal-plan"])


@router.get("/{case_id}/personal-plan")
def personal_plan(case_id: int, extended: bool = False,
                  db: Session = Depends(get_db),
                  family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    country = ((case.country or family.country or "IN") or "IN").upper()
    is_supporter = family.plan_tier == "supporter"
    local_limit = 12 if (extended and is_supporter) else 6
    intl_limit = 12 if (extended and is_supporter) else 6

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
    local = [c for c in scored if (c["country"] or "").upper() == country][:local_limit]
    intl = [c for c in scored if (c["country"] or "").upper() != country][:intl_limit]

    # ---- 2. Schemes for this country vs financial profile ----
    prof_row = db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()
    profile = {f: getattr(prof_row, f) for f in PROFILE_FIELDS} if prof_row else {}
    schemes = (db.query(CoverageScheme)
               .filter(CoverageScheme.country == country).all())
    # Hidden subsidies first — most people never hear about these.
    schemes.sort(key=lambda s: 0 if s.category != "general" else 1)
    scheme_results = sorted(
        (evaluate_scheme(s, profile) for s in schemes),
        key=lambda r: {"eligible": 0, "needs_verification": 1, "not_eligible": 2}.get(r.get("status"), 3),
    )

    # Audience framing: broke vs budgeted get different emphasis (same facts).
    insurance_status = (profile.get("insurance_status") or "unknown").lower()
    has_budget = bool(profile.get("budget_ceiling"))
    if insurance_status in ("uninsured", "unknown") and not has_budget:
        audience_note = ("Focus on the public/charity options below first: government schemes, "
                         "hospital financial-assistance offices, and patient-assistance "
                         "programmes exist precisely for this situation.")
    elif has_budget:
        audience_note = ("With a budget ceiling set, you can also consider private and "
                         "international centres — ask each hospital for an itemised cost "
                         "estimate package before committing; compare against your ceiling.")
    else:
        audience_note = "Your coverage details shape which paths matter most — complete the Finance tab for sharper matching."

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
        "plan_tier": family.plan_tier,
        "audience_note": audience_note,
        "local_centres": local,
        "global_centres": intl,
        "schemes": [{"scheme_name": s.scheme_name, "coverage_limit": s.coverage_limit,
                     "category": s.category,
                     "summary": (s.eligibility_criteria_json or {}).get("summary"),
                     **evaluate_scheme(s, profile)} for s in schemes],
        "scheme_results": scheme_results,
        "options_abroad": {
            "centres": intl[:4],
            "notes": cross_border_notes_for(country),
            "note": ("Participating in another country usually means travel + a medical visa "
                     "and self-pay or special reimbursement. Always start with the destination "
                     "hospital's international patient desk."),
        },
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
