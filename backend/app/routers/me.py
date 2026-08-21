"""DPDP Act 2023 data-principal rights: access (export) and erasure.

- GET  /api/me/export  — full machine-readable copy of everything this family's
  account holds (right to access, s.11).
- DELETE /api/me       — erases the account and all associated records, including
  uploaded files from storage (right to erasure, s.12). Withdrawal of consent is
  made as easy as giving it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_family
from ..database import get_db
from ..models import (Case, CaseFinancialProfile, CasePackage, DecisionFlag,
                      Document, Family, OpinionRequest, TransferRequest)
from ..services.storage import delete_file

router = APIRouter(prefix="/api/me", tags=["dpdp-rights"])


def _case_dict(db: Session, case: Case) -> dict:
    docs = db.query(Document).filter(Document.case_id == case.id).all()
    flags = db.query(DecisionFlag).filter(DecisionFlag.case_id == case.id).all()
    opinions = db.query(OpinionRequest).filter(OpinionRequest.case_id == case.id).all()
    transfers = db.query(TransferRequest).filter(TransferRequest.case_id == case.id).all()
    profile = db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()
    packages = db.query(CasePackage).filter(CasePackage.case_id == case.id).count()
    return {
        "id": case.id,
        "patient_name": case.patient_name,
        "patient_age": case.patient_age,
        "patient_sex": case.patient_sex,
        "cancer_type": case.cancer_type,
        "stage": case.stage,
        "diagnosis_date": case.diagnosis_date.isoformat() if case.diagnosis_date else None,
        "current_status": case.current_status,
        "documents": [{
            "doc_type": d.extracted_doc_type, "source": d.extracted_source,
            "date": d.extracted_date.isoformat() if d.extracted_date else None,
            "findings": d.extracted_key_findings, "has_file": bool(d.file_path),
        } for d in docs],
        "flags": [{"type": f.flag_type, "message": f.message,
                   "acknowledged": f.acknowledged} for f in flags],
        "opinion_requests": [{"status": o.status,
                              "modality": o.opinion_recommended_modality} for o in opinions],
        "transfers": [{"from": t.from_hospital, "to": t.to_hospital, "status": t.status}
                      for t in transfers],
        "financial_profile": {
            "insurance_status": profile.insurance_status if profile else None,
            "insurer_name": profile.insurer_name if profile else None,
            "income_bracket": profile.income_bracket if profile else None,
            "budget_ceiling": profile.budget_ceiling if profile else None,
        } if profile else None,
        "package_versions": packages,
    }


@router.get("/export")
def export_my_data(db: Session = Depends(get_db), family=Depends(get_current_family)):
    cases = db.query(Case).filter(Case.family_id == family.id).all()
    return {
        "account": {"email": family.email, "created_at": family.created_at.isoformat(),
                    "consent_accepted": family.consent_accepted,
                    "consent_at": family.consent_at.isoformat() if family.consent_at else None,
                    "country": family.country, "plan_tier": family.plan_tier},
        "cases": [_case_dict(db, c) for c in cases],
        "notice": "You can request correction or deletion of any of this data at any "
                  "time. Deletion is self-service via DELETE /api/me.",
    }


@router.delete("")
def erase_me(db: Session = Depends(get_db), family=Depends(get_current_family)):
    cases = db.query(Case).filter(Case.family_id == family.id).all()
    for case in cases:
        for doc in db.query(Document).filter(Document.case_id == case.id).all():
            if doc.file_path:
                delete_file(doc.file_path)
            db.delete(doc)
        db.query(DecisionFlag).filter(DecisionFlag.case_id == case.id).delete()
        db.query(OpinionRequest).filter(OpinionRequest.case_id == case.id).delete()
        db.query(CasePackage).filter(CasePackage.case_id == case.id).delete()
        db.query(TransferRequest).filter(TransferRequest.case_id == case.id).delete()
        db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).delete()
        db.delete(case)
    db.delete(family)
    db.commit()
    return {"deleted": True,
            "note": "Account and all associated personal data erased, including uploaded files."}
