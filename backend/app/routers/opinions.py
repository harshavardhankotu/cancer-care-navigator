from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..database import get_db
from ..models import CasePackage, Doctor, Family, OpinionRequest
from ..schemas import DoctorOut, OpinionAction, OpinionCreate, OpinionOut, OpinionRespond
from ..services.packages import create_package_version, render_case_pdf
from ..services.sla import run_sla_check

router = APIRouter(prefix="/api", tags=["opinions"])


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(specialty: str | None = None, remote_only: bool = False,
                 db: Session = Depends(get_db),
                 family: Family = Depends(get_current_family)):
    q = db.query(Doctor)
    if remote_only:
        q = q.filter(Doctor.accepts_remote_case_review.is_(True))
    doctors = q.all()
    if specialty:
        s = specialty.lower()
        doctors = [d for d in doctors if any(s in (t or "").lower() for t in (d.specialty_tags or []))]
    return doctors


@router.post("/cases/{case_id}/opinions")
def create_opinions(case_id: int, body: OpinionCreate, db: Session = Depends(get_db),
                    family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    if not body.doctor_ids:
        raise HTTPException(status_code=400, detail="Select at least one doctor")
    pkg = create_package_version(db, case)
    created = []
    for doctor_id in body.doctor_ids:
        if not db.get(Doctor, doctor_id):
            raise HTTPException(status_code=404, detail=f"Doctor {doctor_id} not found")
        req = OpinionRequest(case_id=case.id, doctor_id=doctor_id, status="drafted",
                             case_package_version_id=pkg.id)
        db.add(req)
        created.append(req)
    db.commit()
    return {"package_version": pkg.version_number,
            "requests": [OpinionOut.model_validate(r).model_dump() for r in created]}


@router.post("/cases/{case_id}/opinions/sla-check")
def sla_check(case_id: int, db: Session = Depends(get_db),
              family: Family = Depends(get_current_family)):
    owned_case(db, family, case_id)
    flagged = run_sla_check(db, case_id)
    return {"flagged_no_response": flagged}


@router.get("/cases/{case_id}/opinions")
def list_opinions(case_id: int, db: Session = Depends(get_db),
                  family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    run_sla_check(db, case.id)
    reqs = db.query(OpinionRequest).filter(OpinionRequest.case_id == case.id).all()
    out = []
    now = datetime.utcnow()
    for r in reqs:
        item = OpinionOut.model_validate(r).model_dump()
        item["overdue"] = bool(
            r.status == "sent" and r.sla_deadline and r.sla_deadline < now
        )
        item["doctor"] = {
            "id": r.doctor.id, "name": r.doctor.name, "hospital": r.doctor.hospital,
            "credentials": r.doctor.credentials, "verified_by": r.doctor.verified_by,
        }
        out.append(item)
    return out


@router.patch("/opinions/{opinion_id}")
def update_opinion(opinion_id: int, body: OpinionAction, db: Session = Depends(get_db),
                   family: Family = Depends(get_current_family)):
    req = db.get(OpinionRequest, opinion_id)
    if not req:
        raise HTTPException(status_code=404, detail="Opinion request not found")
    owned_case(db, family, req.case_id)

    if body.action == "mark_sent":
        if req.status != "drafted":
            raise HTTPException(status_code=400, detail="Only drafted requests can be marked sent")
        req.status = "sent"
        req.sent_at = datetime.utcnow()
        days = (req.doctor.avg_response_time_days or 7) + 2
        req.sla_deadline = req.sent_at + timedelta(days=days)
    elif body.action == "acknowledge":
        if req.status != "sent":
            raise HTTPException(status_code=400,
                                detail="Only sent requests can be acknowledged")
        req.status = "acknowledged"
    elif body.action == "decline":
        if req.status not in ("sent", "acknowledged"):
            raise HTTPException(status_code=400,
                                detail="Only sent or acknowledged requests can be declined")
        req.status = "declined"
    elif body.action == "no_response":
        if req.status not in ("sent", "acknowledged"):
            raise HTTPException(status_code=400,
                                detail="Only sent or acknowledged requests can be marked no_response")
        req.status = "no_response"
    elif body.action == "respond":
        if req.status not in ("sent", "acknowledged", "no_response"):
            raise HTTPException(
                status_code=400,
                detail="Record a response only after the request has been sent.")
        resp = body.response or OpinionRespond()
        req.status = "opinion_received"
        req.responded_at = datetime.utcnow()
        req.opinion_recommended_modality = resp.opinion_recommended_modality
        req.opinion_sequencing_note = resp.opinion_sequencing_note
        req.opinion_caveats = resp.opinion_caveats
        req.opinion_requested_tests = resp.opinion_requested_tests
        _detect_conflicts(db, req.case_id)
    db.commit()
    db.refresh(req)
    return OpinionOut.model_validate(req).model_dump()


def _detect_conflicts(db: Session, case_id: int) -> bool:
    db.flush()
    received = (
        db.query(OpinionRequest)
        .filter(OpinionRequest.case_id == case_id, OpinionRequest.status == "opinion_received",
                OpinionRequest.opinion_recommended_modality.isnot(None))
        .all()
    )
    modalities = {(r.opinion_recommended_modality or "").strip().lower()
                  for r in received if (r.opinion_recommended_modality or "").strip()}
    conflict = len(modalities) > 1
    for r in received:
        r.conflicts_flagged = conflict
    return conflict


@router.get("/cases/{case_id}/opinions/comparison")
def comparison(case_id: int, db: Session = Depends(get_db),
               family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    received = (
        db.query(OpinionRequest)
        .filter(OpinionRequest.case_id == case.id, OpinionRequest.status == "opinion_received")
        .all()
    )
    columns = []
    conflict = any(r.conflicts_flagged for r in received)
    for r in received:
        columns.append({
            "opinion_request_id": r.id,
            "doctor_name": r.doctor.name,
            "hospital": r.doctor.hospital,
            "responded_at": r.responded_at.isoformat() if r.responded_at else None,
            "recommended_modality": r.opinion_recommended_modality,
            "sequencing_note": r.opinion_sequencing_note,
            "caveats": r.opinion_caveats,
            "requested_tests": r.opinion_requested_tests,
            "conflicts_flagged": r.conflicts_flagged,
        })
    return {"conflict_detected": conflict, "columns": columns}


@router.post("/cases/{case_id}/packages")
def generate_package(case_id: int, db: Session = Depends(get_db),
                     family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    pkg = create_package_version(db, case)
    return {"id": pkg.id, "version_number": pkg.version_number,
            "generated_at": pkg.generated_at.isoformat()}


@router.get("/cases/{case_id}/packages")
def list_packages(case_id: int, db: Session = Depends(get_db),
                  family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    pkgs = (db.query(CasePackage).filter(CasePackage.case_id == case.id)
            .order_by(CasePackage.version_number.desc()).all())
    return [{"id": p.id, "version_number": p.version_number,
             "generated_at": p.generated_at.isoformat()} for p in pkgs]


@router.get("/packages/{pkg_id}")
def get_package(pkg_id: int, db: Session = Depends(get_db),
                family: Family = Depends(get_current_family)):
    pkg = db.get(CasePackage, pkg_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    owned_case(db, family, pkg.case_id)
    return {"id": pkg.id, "version_number": pkg.version_number,
            "snapshot_json": pkg.snapshot_json, "generated_at": pkg.generated_at.isoformat()}


@router.get("/packages/{pkg_id}/pdf")
def package_pdf(pkg_id: int, db: Session = Depends(get_db),
                family: Family = Depends(get_current_family)):
    pkg = db.get(CasePackage, pkg_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    owned_case(db, family, pkg.case_id)
    pdf_bytes = render_case_pdf(pkg.snapshot_json, f"Version {pkg.version_number}")
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'attachment; filename="case-{pkg.case_id}-package-v{pkg.version_number}.pdf"'})


@router.post("/packages/{pkg_id}/share-link")
def create_share_link(pkg_id: int, db: Session = Depends(get_db),
                      family: Family = Depends(get_current_family)):
    """Tokenized read-only link so a doctor can view the package WITHOUT an account.

    Zero-cost outreach: the family sends this URL (or the PDF) via WhatsApp/email.
    The token grants read-only access to THIS snapshot only — nothing else.
    """
    import secrets

    pkg = db.get(CasePackage, pkg_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    owned_case(db, family, pkg.case_id)
    if not pkg.share_token:
        pkg.share_token = secrets.token_urlsafe(24)
        db.commit()
    from ..audit import audit
    audit(family.id, "share_create", f"package:{pkg.id}", db=db)
    return {"share_path": f"/package/{pkg.id}/{pkg.share_token}",
            "note": "Anyone with this link can read this snapshot only. Revoke by "
                    "generating a fresh package version and not sharing the old link."}


@router.post("/packages/{pkg_id}/share-revoke")
def revoke_share_link(pkg_id: int, db: Session = Depends(get_db),
                      family: Family = Depends(get_current_family)):
    """Instantly kills a shared link: any old URL stops working (404)."""
    pkg = db.get(CasePackage, pkg_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    owned_case(db, family, pkg.case_id)
    pkg.share_token = None
    db.commit()
    from ..audit import audit
    audit(family.id, "share_revoke", f"package:{pkg.id}", db=db)
    return {"revoked": True,
            "note": "The previous link no longer works. Create a new one anytime."}


# ---- public, unauthenticated share endpoints (token-guarded) ----
public_router = APIRouter(prefix="/api/public/packages", tags=["public-share"])


def _pkg_by_token_or_404(db: Session, pkg_id: int, token: str) -> CasePackage:
    pkg = db.get(CasePackage, pkg_id)
    if not pkg or not pkg.share_token or pkg.share_token != token:
        raise HTTPException(status_code=404, detail="Share link invalid or revoked")
    return pkg


@public_router.get("/{pkg_id}/{token}")
def public_package(pkg_id: int, token: str, db: Session = Depends(get_db)):
    pkg = _pkg_by_token_or_404(db, pkg_id, token)
    return {"id": pkg.id, "version_number": pkg.version_number,
            "generated_at": pkg.generated_at.isoformat(),
            "snapshot_json": pkg.snapshot_json}


@public_router.get("/{pkg_id}/{token}/pdf")
def public_package_pdf(pkg_id: int, token: str, db: Session = Depends(get_db)):
    pkg = _pkg_by_token_or_404(db, pkg_id, token)
    pdf_bytes = render_case_pdf(pkg.snapshot_json, f"Version {pkg.version_number} (shared)")
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'inline; filename="case-package-v{pkg.version_number}.pdf"'})
