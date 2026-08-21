from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..database import get_db
from ..models import Case, DecisionFlag, Family, ForeclosureRule
from ..schemas import CaseCreate, CaseOut, CaseUpdate, FlagOut
from ..services.rules_engine import evaluate_case

router = APIRouter(prefix="/api/cases", tags=["cases"])


def flag_out(db: Session, f: DecisionFlag) -> dict:
    rule = None
    if f.rule:
        rule = {
            "condition_description": f.rule.condition_description,
            "foreclosed_option": f.rule.foreclosed_option,
            "source_guideline": f.rule.source_guideline,
            "source_citation": f.rule.source_citation,
        }
    return FlagOut(
        id=f.id, case_id=f.case_id, flag_type=f.flag_type, message=f.message,
        triggered_at=f.triggered_at, acknowledged=f.acknowledged,
        acknowledged_at=f.acknowledged_at, rule=rule,
    ).model_dump()


@router.post("", response_model=CaseOut)
def create_case(body: CaseCreate, db: Session = Depends(get_db),
                family: Family = Depends(get_current_family)):
    fields = body.model_dump()
    fields["country"] = (fields.pop("country") or "").upper() or family.country or "IN"
    case = Case(family_id=family.id, **fields)
    db.add(case)
    db.commit()
    db.refresh(case)
    evaluate_case(db, case)
    return case


@router.get("")
def list_cases(db: Session = Depends(get_db), family: Family = Depends(get_current_family)):
    cases = db.query(Case).filter(Case.family_id == family.id).order_by(Case.created_at.desc()).all()
    out = []
    for c in cases:
        out.append({
            **CaseOut.model_validate(c).model_dump(),
            "open_flags": db.query(DecisionFlag)
                .filter(DecisionFlag.case_id == c.id, DecisionFlag.acknowledged.is_(False)).count(),
            "document_count": len(c.documents),
        })
    return out


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db),
             family: Family = Depends(get_current_family)):
    return owned_case(db, family, case_id)


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(case_id: int, body: CaseUpdate, db: Session = Depends(get_db),
                family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    evaluate_case(db, case)
    return case


@router.post("/{case_id}/evaluate-rules")
def reevaluate(case_id: int, db: Session = Depends(get_db),
               family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    created = evaluate_case(db, case)
    return {"new_flags": [flag_out(db, f) for f in created]}


@router.get("/{case_id}/flags")
def list_flags(case_id: int, db: Session = Depends(get_db),
               family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    flags = (db.query(DecisionFlag).filter(DecisionFlag.case_id == case.id)
             .order_by(DecisionFlag.triggered_at.desc()).all())
    return [flag_out(db, f) for f in flags]


@router.post("/flags/{flag_id}/acknowledge")
def acknowledge_flag(flag_id: int, db: Session = Depends(get_db),
                     family: Family = Depends(get_current_family)):
    from datetime import datetime

    from ..models import DecisionFlag as DF
    flag = db.get(DF, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    owned_case(db, family, flag.case_id)
    flag.acknowledged = True
    flag.acknowledged_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
