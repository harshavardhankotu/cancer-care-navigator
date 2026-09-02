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

    # Normalized document category matching
    def _doc_text(d):
        return f"{d.extracted_doc_type or ''} {d.extracted_source or ''} {' '.join(d.extracted_key_findings or [])}".lower()

    pathology_keywords = ("pathology", "histopathology", "biopsy", "surgical pathology", "ihc", "histology")
    imaging_keywords = ("imaging", "ct ", "ct-", "mri", "pet", "x-ray", "xray", "scan", "ultrasound", "sonography")
    lab_keywords = ("laboratory", "lab ", "blood", "hematology", "biochemistry", "hemogram", "biomarker", "cbc")

    has_pathology = any(any(k in _doc_text(d) for k in pathology_keywords) for d in docs)
    has_imaging = any(any(k in _doc_text(d) for k in imaging_keywords) for d in docs)
    has_labs = any(any(k in _doc_text(d) for k in lab_keywords) for d in docs)
    has_unconfirmed_dates = any(d.extracted_date is None or bool((d.raw_extraction_json or {}).get("date_unconfirmed")) for d in docs)

    # 5A. Needs Attention: only items that genuinely require action or verification
    needs_attention = []
    for f in flags:
        needs_attention.append({
            "category": "clinical_flag",
            "review_priority": "review_with_clinician",
            "title": f"Sequencing question: {f.rule.condition_description if f.rule else f.message}",
            "action": "Discuss this sequencing question with your treating oncology team before making treatment decisions",
            "tab": "flags",
            "source": f.rule.source_guideline if (f.rule and f.rule.source_guideline) else "Clinical guideline",
        })

    conflict_detected = any(bool(r.conflicts_flagged) for r in opinion_requests)
    if conflict_detected:
        needs_attention.append({
            "category": "opinion_conflict",
            "review_priority": "review_with_clinician",
            "title": "Differing second opinions recorded across specialists",
            "action": "Review the comparison table and discuss differing recommendations with your primary care team or tumor board",
            "tab": "opinions",
        })

    if len(docs) == 0:
        needs_attention.append({
            "category": "records_missing",
            "review_priority": "action_recommended",
            "title": "No diagnostic records uploaded yet",
            "action": "Upload or add your initial pathology reports, imaging scans, or blood tests to build your case timeline",
            "tab": "records",
        })
    elif not has_pathology:
        needs_attention.append({
            "category": "records_missing",
            "review_priority": "action_recommended",
            "title": "Pathology / Biopsy record not yet identified",
            "action": "Locate and add your histopathology report (pathology records are commonly important when preparing a specialist review)",
            "tab": "records",
        })

    if has_unconfirmed_dates:
        needs_attention.append({
            "category": "unconfirmed_dates",
            "review_priority": "verification_recommended",
            "title": "One or more timeline records have unconfirmed dates",
            "action": "Review the Records tab to verify report dates so your clinical timeline is chronologically accurate",
            "tab": "records",
        })

    if not prof_row and len(schemes) > 0:
        needs_attention.append({
            "category": "finance_profile",
            "review_priority": "optional_improvement",
            "title": "Financial profile incomplete",
            "action": "Fill in your insurance and budget details in the Finance tab for sharper scheme matching",
            "tab": "finance",
        })

    # 5B. In Progress: only active processes currently underway
    in_progress = []
    for r in opinion_requests:
        if r.status in ("sent", "acknowledged"):
            is_overdue = bool(r.sla_deadline and r.sla_deadline < datetime.utcnow())
            in_progress.append({
                "category": "second_opinion",
                "title": f"Opinion request with Specialist #{r.doctor_id} ({r.status})",
                "detail": f"Awaiting response (target deadline: {r.sla_deadline.isoformat() if r.sla_deadline else 'Standard SLA'})" + (" — SLA OVERDUE" if is_overdue else ""),
                "is_overdue": is_overdue,
                "tab": "opinions",
            })
    for t in transfers:
        if t.status != "uploaded":
            in_progress.append({
                "category": "transfer",
                "title": f"Hospital transfer: {t.from_hospital or 'Current hospital'} → {t.to_hospital or 'Target centre'}",
                "detail": f"Current status: {t.status} (review packing checklist before travel)",
                "tab": "logistics",
            })

    # 5C. Completed: meaningful milestones actually achieved
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
    uploaded_transfers_count = sum(1 for t in transfers if t.status == "uploaded")
    if uploaded_transfers_count > 0:
        completed.append({"category": "transfers", "title": f"{uploaded_transfers_count} hospital records transfer(s) uploaded"})

    # 5D. Second-Opinion Readiness Model (transparent status and checklist)
    if received_opinions_count > 0:
        opinion_readiness_status = "opinions_received"
    elif any(r.status in ("sent", "acknowledged") for r in opinion_requests):
        opinion_readiness_status = "requests_sent"
    elif any(r.status == "drafted" for r in opinion_requests) and len(packages) > 0:
        opinion_readiness_status = "ready_to_send"
    elif len(packages) > 0:
        opinion_readiness_status = "package_ready"
    elif len(docs) > 0 and not has_pathology:
        opinion_readiness_status = "records_incomplete"
    elif len(docs) > 0:
        opinion_readiness_status = "records_present"
    else:
        opinion_readiness_status = "not_started"

    # 5E. Truly State-Aware Next Steps (Deterministic, max 3–5 items)
    dynamic_next_steps = []
    action_steps = []

    def _add_step(title, explanation, tab, reason=""):
        dynamic_next_steps.append(f"{title}: {explanation}")
        action_steps.append({
            "title": title,
            "explanation": explanation,
            "tab": tab,
            "reason": reason,
        })

    # Rule 1: No records -> upload initial record
    if len(docs) == 0:
        _add_step("Upload initial record", "Upload or add your first pathology, imaging, or laboratory record to build your case timeline", "records", "A clinical timeline starts with your diagnostic records")
    # Rule 2: Pathology missing -> locate pathology
    elif not has_pathology:
        _add_step("Add pathology record", "Locate and upload your biopsy or histopathology report", "records", "Pathology records are commonly needed for specialist reviews")

    # Rule 3: Clinical sequencing flags open -> discuss with team
    if flags:
        _add_step("Review sequencing questions", "Discuss the flagged sequencing question(s) with your treating oncology team before making treatment decisions", "flags", "Certain treatments may foreclosed options if sequencing is not verified")

    # Rule 4: Records exist but package absent -> create package
    if len(docs) > 0 and len(packages) == 0:
        _add_step("Create case package", "Compile an immutable case package snapshot in Second Opinions to prepare for consultations", "opinions", "Having a single shareable package simplifies doctor consultations")

    # Rule 5: Drafted opinions exist -> send to specialists
    if any(r.status == "drafted" for r in opinion_requests):
        _add_step("Send drafted requests", "Send your prepared case package link to consulting specialists and mark them sent", "opinions", "Parallel review reduces sequential delays")

    # Rule 6: Opinions sent -> monitor SLA
    if any(r.status in ("sent", "acknowledged") for r in opinion_requests):
        _add_step("Monitor opinion replies", "Check response progress against target SLA deadlines", "opinions", "Follow up if specialist response is delayed")

    # Rule 7: Conflicting opinions -> discuss with care team
    if conflict_detected:
        _add_step("Review opinion differences", "Bring differing specialist recommendations to your primary care team or tumor board to discuss", "opinions", "Comparing modalities helps you ask focused questions")

    # Rule 8: Transfer in progress -> packing checklist
    if any(t.status != "uploaded" for t in transfers):
        _add_step("Prepare transfer records", "Review the physical transfer checklist in Logistics to confirm materials requested by the receiving centre", "logistics", "Receiving centres often require original slides and DICOM media")

    # Rule 9: Financial verification if eligible schemes exist
    eligible_schemes = [s for s in scheme_results if s["status"] in ("eligible", "needs_verification")]
    if eligible_schemes and prof_row:
        _add_step("Verify coverage schemes", "Check official verification pathways and required documents on government portals linked below", "finance", "Scheme criteria change; official portals confirm final eligibility")

    # Rule 10: Fallback exploration step if early in journey
    if len(dynamic_next_steps) < 3:
        _add_step("Explore accredited centres", "Review objective public facts for specialized cancer centres in your region", "centers", "Public accreditation and service capabilities help identify care options")

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
            "statement": "Records identified in your case profile by category.",
        },
        "second_opinion_readiness": {
            "status": opinion_readiness_status,
            "ready": len(packages) > 0 and has_pathology,
            "has_records": len(docs) > 0,
            "has_pathology": has_pathology,
            "has_package": len(packages) > 0,
            "open_flags_count": len(flags),
            "checklist": [
                {"item": "Pathology / biopsy report", "present": has_pathology},
                {"item": "Imaging scans (CT/PET/MRI)", "present": has_imaging},
                {"item": "Laboratory / blood reports", "present": has_labs},
                {"item": "Immutable case snapshot package", "present": len(packages) > 0},
                {"item": "Specialist consultation questions", "present": len(questions) > 0},
            ],
        },
        "next_steps": dynamic_next_steps[:4],
        "action_steps": action_steps[:4],
        "disclaimer": ("This plan organises public information around YOUR case. It is not "
                       "medical advice; decisions rest with you and your treating doctors."),
    }
    return plan
