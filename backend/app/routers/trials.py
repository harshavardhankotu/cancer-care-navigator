from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_family
from ..database import get_db
from ..models import Family
from ..services.trials import search_trials

router = APIRouter(prefix="/api/trials", tags=["trials"])


@router.get("/search")
def search(cancer_type: str | None = None, biomarkers: str | None = None,
           live: bool = True, db: Session = Depends(get_db),
           family: Family = Depends(get_current_family)):
    bm_list = [b.strip() for b in (biomarkers or "").split(",") if b.strip()]
    result = search_trials(db, cancer_type, bm_list, include_live=live)
    result["disclaimer"] = ("Trial eligibility is decided by the trial team, not by this tool. "
                            "Discuss participation with your treating oncologist.")
    return result
