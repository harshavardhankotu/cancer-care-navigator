from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_token, get_current_family, hash_password, verify_password
from ..database import get_db
from ..models import Family
from ..schemas import FamilyCreate, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(body: FamilyCreate, db: Session = Depends(get_db)):
    if "@" not in body.email or len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Valid email and 6+ char password required")
    existing = db.query(Family).filter(Family.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    family = Family(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(family)
    db.commit()
    db.refresh(family)
    return TokenOut(token=create_token(family.id), email=family.email)


@router.post("/login", response_model=TokenOut)
def login(body: FamilyCreate, db: Session = Depends(get_db)):
    family = db.query(Family).filter(Family.email == body.email.lower()).first()
    if not family or not verify_password(body.password, family.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(token=create_token(family.id), email=family.email)


@router.get("/me")
def me(family: Family = Depends(get_current_family)):
    return {"id": family.id, "email": family.email}
