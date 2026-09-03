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

from datetime import datetime

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

    # 5D. 7-State Second-Opinion Readiness Lifecycle Model
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

    # 5E. Truly State-Aware Next Steps (Deterministic priority order, max 4 items)
    action_steps = []

    def _add_step(title, explanation, tab, reason=""):
        # Prevent duplicate steps
        if not any(s["title"] == title for s in action_steps):
            action_steps.append({
                "title": title,
                "explanation": explanation,
                "tab": tab,
                "reason": reason,
            })

    # Priority 1: Unresolved clinical sequencing questions
    if flags:
        _add_step(
            "Review sequencing questions",
            "Discuss the flagged sequencing question(s) with your treating oncology team before making treatment decisions.",
            "flags",
            "Some treatment pathways can depend on diagnostic information being available first.",
        )

    # Priority 2: Missing or unconfirmed core records
    if len(docs) == 0:
        _add_step(
            "Add initial diagnostic record",
            "Upload or add your first pathology, imaging, or laboratory report to establish your case timeline.",
            "records",
            "A clinical timeline starts with your diagnostic records.",
        )
    elif not has_pathology:
        _add_step(
            "Add pathology report",
            "Locate and upload your biopsy or histopathology report to document tissue confirmation.",
            "records",
            "Pathology and biomarker records are commonly requested when specialists review a case.",
        )

    if has_unconfirmed_dates:
        _add_step(
            "Verify timeline report dates",
            "Check original report dates for records marked unconfirmed so your clinical timeline is chronologically accurate.",
            "records",
            "Accurate report dates prevent confusion regarding disease progression and treatment intervals.",
        )

    # Priority 3: Overdue specialist responses or conflicting opinions
    has_overdue_opinion = any(
        bool(r.sla_deadline and r.sla_deadline < datetime.utcnow())
        for r in opinion_requests
        if r.status in ("sent", "acknowledged")
    )
    if has_overdue_opinion:
        _add_step(
            "Follow up on specialist opinion",
            "One or more second-opinion requests have passed their target response window; consider contacting the clinic coordinator.",
            "opinions",
            "Tracking target turnaround times helps prevent open-ended consultation delays.",
        )

    if conflict_detected:
        _add_step(
            "Review opinion differences",
            "Specialist opinions suggest differing recommendations; discuss the differences with your treating clinical team or multidisciplinary tumor board.",
            "opinions",
            "Comparing treatment modalities helps you ask focused questions about sequencing and options.",
        )

    # Priority 4: Active hospital transfer coordination
    if any(t.status != "uploaded" for t in transfers):
        _add_step(
            "Prepare transfer records",
            "Confirm physical materials (e.g. slides, imaging media) requested by the receiving hospital before travel.",
            "logistics",
            "Receiving centres commonly require primary diagnostic materials before outpatient evaluation.",
        )

    # Priority 5: Second-opinion preparation or dispatch
    if opinion_readiness_status == "ready_to_send":
        _add_step(
            "Send drafted requests",
            "Send your prepared case package link to consulting specialists and mark the requests as sent.",
            "opinions",
            "Parallel review allows consulting specialists to evaluate your case concurrently.",
        )
    elif opinion_readiness_status == "package_ready":
        _add_step(
            "Select specialists for second opinion",
            "Your case snapshot is compiled; select 1–2 consulting specialists in Second Opinions to prepare requests.",
            "opinions",
            "Preparing consultation requests in advance streamlines specialist outreach.",
        )
    elif len(docs) > 0 and len(packages) == 0:
        _add_step(
            "Create case package snapshot",
            "Compile an immutable case package snapshot in Second Opinions to prepare for consultations.",
            "opinions",
            "Having a single shareable snapshot simplifies specialist reviews without requiring an account.",
        )

    # Priority 6: Financial scheme verification
    eligible_schemes = [s for s in scheme_results if s["status"] in ("eligible", "needs_verification")]
    if eligible_schemes and prof_row:
        _add_step(
            "Verify coverage schemes",
            "Check official verification pathways and required documents on government portals linked below.",
            "finance",
            "Scheme criteria change periodically; official portals provide definitive empanelment and claim rules.",
        )

    # Priority 7: Context-dependent fallback (only if no urgent or in-progress action items exist)
    if len(action_steps) == 0:
        _add_step(
            "Review care options",
            "Review objective public information about accredited centres, coverage pathways, and navigation options when you are ready.",
            "centers",
            "Objective public information can help you prepare questions for your treating clinical team.",
        )

    selected_actions = action_steps[:4]
    dynamic_next_steps = [f"{a['title']}: {a['explanation']}" for a in selected_actions]

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
            "lifecycle": "7-state second-opinion readiness lifecycle",
            "ready": opinion_readiness_status in ("package_ready", "ready_to_send"),
            "ready_description": (
                "Snapshot package compiled and ready for specialist outreach."
                if opinion_readiness_status in ("package_ready", "ready_to_send")
                else "Case is not currently in the pre-dispatch preparation stage."
            ),
            "has_records": len(docs) > 0,
            "has_pathology": has_pathology,
            "has_package": len(packages) > 0,
            "open_flags_count": len(flags),
            "checklist": [
                {
                    "category": "Pathology / biopsy report",
                    "item": "Pathology / biopsy report",
                    "present": has_pathology,
                    "status": "present" if has_pathology else "not_identified",
                },
                {
                    "category": "Imaging scans (CT/PET/MRI)",
                    "item": "Imaging scans (CT/PET/MRI)",
                    "present": has_imaging,
                    "status": "present" if has_imaging else "not_identified",
                },
                {
                    "category": "Laboratory / blood reports",
                    "item": "Laboratory / blood reports",
                    "present": has_labs,
                    "status": "present" if has_labs else "not_identified",
                },
                {
                    "category": "Immutable case snapshot package",
                    "item": "Immutable case snapshot package",
                    "present": len(packages) > 0,
                    "status": "compiled" if len(packages) > 0 else "not_created",
                },
                {
                    "category": "Specialist consultation questions",
                    "item": "Specialist consultation questions",
                    "present": len(questions) > 0,
                    "status": "reviewed" if len(questions) > 0 else "none_queued",
                },
            ],
        },
        "next_steps": dynamic_next_steps,
        "action_steps": selected_actions,
        "disclaimer": ("This plan organises public information around YOUR case. It is not "
                       "medical advice; decisions rest with you and your treating doctors."),
    }
    return plan
