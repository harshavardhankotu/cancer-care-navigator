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
from ..models import (CaseFinancialProfile, CasePackage, CoverageScheme,
                      DecisionFlag, Document, Family, OpinionRequest,
                      SpecialistCenter, TransferRequest)
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

    # ---- 5. Journey Navigation State (Needs Attention / In Progress / Completed) ----
    docs = db.query(Document).filter(Document.case_id == case.id).all()
    opinion_requests = db.query(OpinionRequest).filter(OpinionRequest.case_id == case.id).all()
    transfers = db.query(TransferRequest).filter(TransferRequest.case_id == case.id).all()
    packages = db.query(CasePackage).filter(CasePackage.case_id == case.id).all()

    # Document classification check
    has_pathology = any("pathology" in (d.extracted_doc_type or "").lower() or "biopsy" in (d.extracted_doc_type or "").lower() for d in docs)
    has_imaging = any(any(k in (d.extracted_doc_type or "").lower() for k in ("imaging", "scan", "mri", "ct", "pet", "x-ray")) for d in docs)
    has_labs = any("lab" in (d.extracted_doc_type or "").lower() or "blood" in (d.extracted_doc_type or "").lower() for d in docs)
    has_unconfirmed_dates = any(d.extracted_date is None or (d.raw_extraction_json or {}).get("date_unconfirmed") for d in docs)

    needs_attention = []
    for f in flags:
        needs_attention.append({
            "category": "clinical_flag",
            "urgency": "high",
            "title": f"Time-sensitive question: {f.rule.condition_description if f.rule else f.message}",
            "action": "Discuss with your oncologist before treatment sequencing",
            "tab": "flags",
        })

    # Check for opinion conflict
    conflict_detected = any(bool(r.conflicts_flagged) for r in opinion_requests)
    if conflict_detected:
        needs_attention.append({
            "category": "opinion_conflict",
            "urgency": "high",
            "title": "Differing second opinions recorded across specialists",
            "action": "Review the comparison table and discuss differing recommendations with your primary care team or tumor board",
            "tab": "opinions",
        })

    if len(docs) == 0:
        needs_attention.append({
            "category": "records_missing",
            "urgency": "medium",
            "title": "No diagnostic records uploaded yet",
            "action": "Upload pathology reports, imaging scans, and blood work to build your case timeline",
            "tab": "records",
        })
    elif not has_pathology:
        needs_attention.append({
            "category": "records_missing",
            "urgency": "medium",
            "title": "Pathology / Biopsy report not yet identified",
            "action": "Upload your histopathology report (second opinions and tumor boards require it)",
            "tab": "records",
        })

    if not prof_row:
        needs_attention.append({
            "category": "finance_profile",
            "urgency": "low",
            "title": "Financial profile incomplete",
            "action": "Fill in your insurance and budget details in the Finance tab for sharper scheme matching",
            "tab": "finance",
        })

    # In progress items
    in_progress = []
    for r in opinion_requests:
        if r.status in ("sent", "acknowledged"):
            in_progress.append({
                "category": "second_opinion",
                "title": f"Opinion request with Specialist #{r.doctor_id} ({r.status})",
                "detail": f"Awaiting response (target deadline: {r.sla_deadline.isoformat() if r.sla_deadline else 'Standard SLA'})",
                "tab": "opinions",
            })
    for t in transfers:
        if t.status != "uploaded":
            in_progress.append({
                "category": "transfer",
                "title": f"Hospital transfer: {t.from_hospital or 'Current hospital'} → {t.to_hospital or 'Target centre'}",
                "detail": f"Current status: {t.status}",
                "tab": "logistics",
            })

    # Completed items
    completed = [
        {"category": "case_init", "title": f"Case profile created: {case.patient_name} ({case.cancer_type})"}
    ]
    if len(docs) > 0:
        completed.append({"category": "records", "title": f"{len(docs)} document(s) added to chronological timeline"})
    if len(packages) > 0:
        completed.append({"category": "package", "title": f"{len(packages)} immutable case package snapshot(s) compiled"})
    ack_flags_count = db.query(DecisionFlag).filter(DecisionFlag.case_id == case.id, DecisionFlag.acknowledged.is_(True)).count()
    if ack_flags_count > 0:
        completed.append({"category": "flags", "title": f"{ack_flags_count} clinical sequencing flag(s) acknowledged"})
    received_opinions_count = sum(1 for r in opinion_requests if r.status == "opinion_received")
    if received_opinions_count > 0:
        completed.append({"category": "opinions", "title": f"{received_opinions_count} specialist second opinion(s) recorded"})

    # Dynamic Next Steps tailored to patient state
    dynamic_next_steps = []
    if len(docs) == 0:
        dynamic_next_steps.append("Upload your initial biopsy/pathology report and scans in the Records tab")
    if flags:
        dynamic_next_steps.append("Review the flagged questions with your oncologist before starting irreversible treatment")
    if len(docs) > 0 and len(packages) == 0:
        dynamic_next_steps.append("Compile an immutable case package (Second Opinions tab) to prepare for specialist consultations")
    if any(r.status == "drafted" for r in opinion_requests):
        dynamic_next_steps.append("Send your drafted second opinion requests to consulting oncologists")
    if conflict_detected:
        dynamic_next_steps.append("Bring the differing opinion reports to your primary treating oncologist to review differences")
    dynamic_next_steps.extend([
        f"Shortlist 1–2 centres above and ask your current hospital for records transfer",
        "Send your case package (Second Opinions tab) to 2–3 doctors in parallel",
        "Verify scheme eligibility at the official portal — links are on each scheme card",
        "Check recruiting trials with your oncologist — participation is always voluntary",
    ])
    # Deduplicate while preserving order
    seen_steps = set()
    deduped_next_steps = []
    for s in dynamic_next_steps:
        if s not in seen_steps:
            seen_steps.add(s)
            deduped_next_steps.append(s)

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
        "needs_attention": needs_attention,
        "in_progress": in_progress,
        "completed": completed,
        "record_readiness": {
            "total_documents": len(docs),
            "has_pathology": has_pathology,
            "has_imaging": has_imaging,
            "has_labs": has_labs,
            "has_unconfirmed_dates": has_unconfirmed_dates,
        },
        "second_opinion_readiness": {
            "ready": len(docs) > 0 and len(packages) > 0,
            "has_records": len(docs) > 0,
            "has_package": len(packages) > 0,
            "open_flags_count": len(flags),
        },
        "next_steps": deduped_next_steps[:6],
        "disclaimer": ("This plan organises public information around YOUR case. It is not "
                       "medical advice; decisions rest with you and your treating doctors."),
    }
    return plan
