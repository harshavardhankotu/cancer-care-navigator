import hashlib
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import SECRET_KEY, TOKEN_ALGORITHM, TOKEN_EXPIRE_HOURS
from .database import get_db
from .models import Case, Family

# ---- Simple in-memory brute-force limiter ----
# Fine for a single process. Swap for Redis-backed counting when running
# multiple workers/replicas (documented in README).
_attempts: dict[str, deque] = defaultdict(deque)


def is_rate_limited(key: str, max_attempts: int, window_seconds: int) -> bool:
    """Records an attempt and returns True when over the limit."""
    now = datetime.now(timezone.utc)
    q = _attempts[key]
    cutoff = now - timedelta(seconds=window_seconds)
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= max_attempts:
        return True
    q.append(now)
    return False


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return secrets.compare_digest(dk.hex(), expected_hex)
    except Exception:
        return False


def create_token(family_id: int) -> str:
    payload = {
        "sub": str(family_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=TOKEN_ALGORITHM)


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None


def get_current_family(authorization: str | None = Header(default=None),
                       db: Session = Depends(get_db)) -> Family:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    family_id = decode_token(authorization.split(" ", 1)[1].strip())
    if family_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    family = db.get(Family, family_id)
    if not family:
        raise HTTPException(status_code=401, detail="Account not found")
    return family


def owned_case(db: Session, family: Family, case_id: int) -> Case:
    case = db.get(Case, case_id)
    if not case or case.family_id != family.id:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
