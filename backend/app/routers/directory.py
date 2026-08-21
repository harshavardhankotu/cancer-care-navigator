from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..database import get_db
from ..models import (Family, HospitalNote, SpecialistCenter, TransferRequest,
                      WaitTimeReport)
from ..schemas import CenterOut, TransferIn, TransferOut, WaitReportIn
from ..seed_data import PUBLIC_CHECK_LINKS

router = APIRouter(prefix="/api", tags=["directory"])

# ---- Transparent, fact-based comparison (NOT a quality rating) ----
# Score = sum of verifiable public facts only. Full breakdown is returned with
# every centre so patients can see exactly where each point comes from.
# The "institutional_designation" factor is the closest citable proxy for a
# centre's history/standing: designation programmes (e.g., NCI Comprehensive,
# DKG CCC, national flagship institutes) publish their criteria and member lists.
SCORE_WEIGHTS = {
    "public_or_nonprofit_ownership": 3,
    "national_accreditation_noted": 2,
    "scheme_empanelment_noted": 2,
    "capability_breadth": 3,  # scaled: 1-4 caps=1, 5-7=2, 8+=3
    "institutional_designation": 4,
}
NOTE_TYPE_TO_FACTOR = {
    "ownership": "public_or_nonprofit_ownership",
    "accreditation": "national_accreditation_noted",
    "scheme_empanelment": "scheme_empanelment_noted",
    "designation": "institutional_designation",
}


def _is_public_nonprofit(detail: str) -> bool:
    d = detail.lower()
    return any(k in d for k in (
        "government", "public-funded", "public funded", "non-profit", "nonprofit",
        "charitable trust", "not-for-profit", "state-aided", "institute of national importance"))


def _designation_points(detail: str) -> int:
    """Tiered by how selective the programme is: NCI 'Comprehensive' is +4,
    other national/designation programmes +3."""
    full = SCORE_WEIGHTS["institutional_designation"]
    return full if "comprehensive" in detail.lower() else full - 1


def _score_center(center: SpecialistCenter, notes: list[HospitalNote]) -> dict:
    breakdown = {k: 0 for k in SCORE_WEIGHTS}
    caps = len(center.capabilities or [])
    breakdown["capability_breadth"] = 1 if caps <= 4 else (2 if caps <= 7 else 3)
    for n in notes:
        factor = NOTE_TYPE_TO_FACTOR.get(n.note_type)
        if not factor or breakdown[factor] > 0:  # first matching note scores; extras don't stack
            continue
        if n.note_type == "ownership" and _is_public_nonprofit(n.detail):
            breakdown[factor] = SCORE_WEIGHTS[factor]
        elif n.note_type == "designation":
            breakdown[factor] = _designation_points(n.detail)
        elif n.note_type in ("accreditation", "scheme_empanelment"):
            breakdown[factor] = SCORE_WEIGHTS[factor]
    total = sum(breakdown.values())
    return {"total": total, "max": sum(SCORE_WEIGHTS.values()), "breakdown": breakdown}


@router.get("/centers")
def list_centers(cancer_type: str | None = None, capability: str | None = None,
                 country: str | None = None, sort: str = "score",
                 db: Session = Depends(get_db)):
    centers = db.query(SpecialistCenter).all()
    if country:
        ctry = country.upper()
        centers = [c for c in centers if (c.country or "").upper() == ctry]
    if cancer_type:
        ct = cancer_type.lower()
        centers = [c for c in centers if any(ct in t.lower() or t.lower() in ct
                                             for t in (c.cancer_types or ["any"])) or "any" in (c.cancer_types or [])]
    if capability:
        cap = capability.lower()
        centers = [c for c in centers if any(cap in x.lower() for x in (c.capabilities or []))]

    out = []
    for c in centers:
        notes = db.query(HospitalNote).filter(HospitalNote.center_id == c.id).all()
        out.append({
            **CenterOut.model_validate(c).model_dump(),
            "country": c.country,
            "notes": [{
                "note_type": n.note_type, "detail": n.detail,
                "source_name": n.source_name, "source_url": n.source_url,
                "as_of_date": n.as_of_date.isoformat() if n.as_of_date else None,
            } for n in notes],
            "objective_score": _score_center(c, notes),
        })
    if sort == "score":
        out.sort(key=lambda x: (-x["objective_score"]["total"], (x["name"] or "").lower()))
    else:
        out.sort(key=lambda x: ((x.get("country") or "").lower(), (x["name"] or "").lower()))
    return out


@router.get("/centers/methodology")
def ranking_methodology():
    """Full transparency: what the score counts, what it ignores, and where
    patients can verify ANY hospital themselves."""
    return {
        "title": "How centres are compared — full transparency",
        "principles": [
            "We use ONLY objective, publicly citable facts — never user reviews, which are "
            "easy to buy and game.",
            "'History & standing' is proxied by institutional designation programmes (NCI "
            "Comprehensive Cancer Centers, DKG-certified CCCs, national flagship institutes) "
            "whose criteria and member lists are published — not by anecdotes.",
            "This is NOT a quality ranking and NOT medical advice. A high score does not mean "
            "'best for your case' — that decision belongs to you and your treating doctors.",
            "Individual doctors are deliberately NOT scored. Doctor ratings invite gaming and "
            "legal risk; instead we show verifiable credential fields once curated.",
        ],
        "weights": SCORE_WEIGHTS,
        "designation_tiers": {
            "+4": "NCI-Designated COMPREHENSIVE Cancer Center (US NCI list)",
            "+3": "Other national/designation programmes (DKG CCC, national institutes, OECI-accredited)",
        },
        "what_we_cannot_measure": [
            "Clinical outcomes per hospital (no country publishes comparable per-hospital cancer outcomes)",
            "Doctor skill (deferred to NMC/state council registers during human curation)",
            "Your personal clinical situation",
        ],
        "verify_any_hospital_yourself": PUBLIC_CHECK_LINKS,
        "disclaimer": ("Facts change; every note carries its source link and as-of date. "
                       "Always verify at the source before making decisions."),
    }


@router.get("/centers/wait-summary")
def wait_summary(db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=90)
    rows = (
        db.query(WaitTimeReport.center_name,
                 func.avg(WaitTimeReport.reported_wait_days).label("avg_days"),
                 func.count(WaitTimeReport.id).label("reports"))
        .filter(WaitTimeReport.reported_at >= cutoff)
        .group_by(WaitTimeReport.center_name)
        .all()
    )
    return [{"center_name": r.center_name, "avg_recent_wait_days": round(float(r.avg_days), 1),
             "report_count": int(r.reports), "window": "last 90 days"} for r in rows]


@router.post("/wait-reports")
def add_wait_report(body: WaitReportIn, db: Session = Depends(get_db),
                    family: Family = Depends(get_current_family)):
    if body.reported_wait_days < 0:
        raise HTTPException(status_code=400, detail="Wait days must be >= 0")
    report = WaitTimeReport(center_name=body.center_name.strip(),
                            reported_wait_days=body.reported_wait_days,
                            reported_by_family_id=family.id)
    db.add(report)
    db.commit()
    return {"ok": True, "id": report.id}


@router.post("/cases/{case_id}/transfers", response_model=TransferOut)
def create_transfer(case_id: int, body: TransferIn, db: Session = Depends(get_db),
                    family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    transfer = TransferRequest(case_id=case.id, from_hospital=body.from_hospital,
                               to_hospital=body.to_hospital, status="requested")
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("/cases/{case_id}/transfers", response_model=list[TransferOut])
def list_transfers(case_id: int, db: Session = Depends(get_db),
                   family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    return (db.query(TransferRequest).filter(TransferRequest.case_id == case.id)
            .order_by(TransferRequest.requested_at.desc()).all())


@router.patch("/transfers/{transfer_id}", response_model=TransferOut)
def update_transfer(transfer_id: int, status: str, db: Session = Depends(get_db),
                    family: Family = Depends(get_current_family)):
    from ..models import Case as CaseModel
    transfer = db.get(TransferRequest, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer request not found")
    case = db.get(CaseModel, transfer.case_id)
    if not case or case.family_id != family.id:
        raise HTTPException(status_code=404, detail="Transfer request not found")
    if status not in ("requested", "received", "uploaded"):
        raise HTTPException(status_code=400, detail="Invalid status")
    transfer.status = status
    db.commit()
    db.refresh(transfer)
    return transfer
