"""Minimal audit trail (GDPR Art. 30/32 accountability).

Logs security-relevant events with NO personal content beyond the account id:
register, login_fail, export, erase, share_create, share_revoke.

If an active `db` session is passed, the row joins that transaction (avoids
SQLite write locks mid-request). Otherwise a dedicated short session is used.
"""

from .database import SessionLocal
from .models import AuditLog


def audit(family_id: int | None, action: str, detail: str | None = None,
          db=None) -> None:
    try:
        if db is not None:
            db.add(AuditLog(family_id=family_id, action=action, detail=detail))
            return  # caller's commit covers us
        with SessionLocal() as own:
            own.add(AuditLog(family_id=family_id, action=action, detail=detail))
            own.commit()
    except Exception:
        pass  # auditing must never break the request path
