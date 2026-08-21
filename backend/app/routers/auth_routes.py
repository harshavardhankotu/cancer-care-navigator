from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import (create_token, get_current_family, hash_password,
                    is_rate_limited, verify_password)
from ..database import get_db
from ..models import Family
from ..schemas import FamilyCreate, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

_WEAK_PASSWORDS = {
    "password", "password1", "password123", "12345678", "123456789",
    "1234567890", "qwertyuiop", "letmein123", "iloveyou1", "admin12345",
    "welcome1", "abc12345",
}


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400,
                            detail="Password must be at least 8 characters.")
    if password.lower() in _WEAK_PASSWORDS:
        raise HTTPException(status_code=400,
                            detail="That password is too common. Choose something unique.")


@router.post("/register", response_model=TokenOut)
def register(body: FamilyCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"reg:{ip}", max_attempts=30, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Too many signups from this network. Try later.")
    if "@" not in body.email or len(body.password) < 8:
        raise HTTPException(status_code=400,
                            detail="Valid email and 8+ character password required")
    _validate_password(body.password)
    if not body.consent_accepted:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent is required before we process any personal data "
                   "(Digital Personal Data Protection Act, 2023). Please accept the "
                   "privacy notice to register.")
    existing = db.query(Family).filter(Family.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    family = Family(email=body.email.lower(), password_hash=hash_password(body.password),
                    consent_accepted=True, consent_at=datetime.utcnow(),
                    country=(body.country or "").upper() or None)
    db.add(family)
    db.commit()
    db.refresh(family)
    return TokenOut(token=create_token(family.id), email=family.email)


@router.post("/login", response_model=TokenOut)
def login(body: FamilyCreate, request: Request, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login:{ip}:{email}", max_attempts=10, window_seconds=300):
        raise HTTPException(status_code=429,
                            detail="Too many attempts. Wait a few minutes and try again.")
    family = db.query(Family).filter(Family.email == email).first()
    if not family or not verify_password(body.password, family.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(token=create_token(family.id), email=family.email)


@router.get("/me")
def me(family: Family = Depends(get_current_family)):
    return {"id": family.id, "email": family.email}
