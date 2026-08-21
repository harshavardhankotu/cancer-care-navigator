from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..database import get_db
from ..models import (Family, SpecialistCenter, TransferRequest, WaitTimeReport)
from ..schemas import CenterOut, TransferIn, TransferOut, WaitReportIn

router = APIRouter(prefix="/api", tags=["directory"])


@router.get("/centers", response_model=list[CenterOut])
def list_centers(cancer_type: str | None = None, capability: str | None = None,
                 db: Session = Depends(get_db)):
    centers = db.query(SpecialistCenter).all()
    if cancer_type:
        ct = cancer_type.lower()
        centers = [c for c in centers if any(ct in t.lower() or t.lower() in ct
                                             for t in (c.cancer_types or ["any"])) or "any" in (c.cancer_types or [])]
    if capability:
        cap = capability.lower()
        centers = [c for c in centers if any(cap in x.lower() for x in (c.capabilities or []))]
    return centers


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
