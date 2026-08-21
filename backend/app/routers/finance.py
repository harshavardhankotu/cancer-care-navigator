from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..config import DISCLAIMER
from ..database import get_db
from ..models import (CaseFinancialProfile, CoverageScheme, DecisionFlag,
                      Family, PatientAssistanceProgram)
from ..schemas import CoverageCheckIn, FinProfileIn, FinProfileOut
from ..services.eligibility import evaluate_scheme, run_case_match

router = APIRouter(prefix="/api", tags=["finance"])


@router.put("/cases/{case_id}/financial-profile", response_model=FinProfileOut)
def upsert_profile(case_id: int, body: FinProfileIn, db: Session = Depends(get_db),
                   family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    prof = db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()
    if not prof:
        prof = CaseFinancialProfile(case_id=case.id)
        db.add(prof)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(prof, field, value)
    db.commit()
    db.refresh(prof)
    return prof


@router.get("/cases/{case_id}/financial-profile", response_model=FinProfileOut | None)
def get_profile(case_id: int, db: Session = Depends(get_db),
                family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    return db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()


@router.post("/cases/{case_id}/coverage-match")
def coverage_match(case_id: int, db: Session = Depends(get_db),
                   family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    result = run_case_match(db, case)
    open_gap = (
        db.query(DecisionFlag)
        .filter(DecisionFlag.case_id == case.id, DecisionFlag.flag_type == "coverage_gap",
                DecisionFlag.acknowledged.is_(False))
        .first()
    )
    if result["gaps"] and not open_gap:
        flag = DecisionFlag(case_id=case.id, flag_type="coverage_gap",
                            message="\n".join(result["gaps"]))
        db.add(flag)
        db.commit()
    result["disclaimer"] = DISCLAIMER
    return result


@router.get("/schemes")
def list_schemes(country: str | None = None, db: Session = Depends(get_db)):
    schemes = db.query(CoverageScheme).all()
    if country:
        ctry = country.upper()
        schemes = [s for s in schemes if (s.country or "").upper() == ctry]
    return [{
        "id": s.id, "scheme_name": s.scheme_name, "country": s.country,
        "eligibility_summary": (s.eligibility_criteria_json or {}).get("summary"),
        "covered_treatments": s.covered_treatments, "network_hospitals": s.network_hospitals,
        "coverage_limit": s.coverage_limit, "exclusions": s.exclusions,
        "last_verified_date": s.last_verified_date.isoformat() if s.last_verified_date else None,
    } for s in schemes]


@router.get("/assistance-programs")
def list_paps(db: Session = Depends(get_db)):
    paps = db.query(PatientAssistanceProgram).all()
    return [{"id": p.id, "drug_name": p.drug_name, "manufacturer": p.manufacturer,
             "program_type": p.program_type, "eligibility_criteria": p.eligibility_criteria,
             "application_process": p.application_process, "verified_by": p.verified_by,
             "last_verified_date": p.last_verified_date.isoformat() if p.last_verified_date else None}
            for p in paps]


@router.post("/coverage-check")
def public_coverage_check(body: CoverageCheckIn, db: Session = Depends(get_db)):
    profile = {"insurance_status": body.insurance_status,
               "income_bracket": body.income_bracket,
               "employment": body.employment}
    schemes = db.query(CoverageScheme).all()
    if body.country:
        ctry = body.country.upper()
        schemes = [s for s in schemes if (s.country or "").upper() == ctry]
    results = [evaluate_scheme(s, profile) for s in schemes]
    results.sort(key=lambda r: {"eligible": 0, "needs_verification": 1, "not_eligible": 2}[r["status"]])
    return {
        "country": (body.country or "").upper() or None,
        "results": results,
        "disclaimer": DISCLAIMER + " Scheme parameters change; verify on the official portals "
                                   "linked in this app. Eligibility is always confirmed by the "
                                   "scheme itself, never by this tool.",
    }
