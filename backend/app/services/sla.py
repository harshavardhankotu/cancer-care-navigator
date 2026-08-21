"""SLA checking for opinion requests.

MVP: on-page-load check instead of a background job. Any request still in
'sent' status past its sla_deadline is moved to 'no_response'.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import OpinionRequest


def run_sla_check(db: Session, case_id: int) -> int:
    now = datetime.utcnow()
    overdue = (
        db.query(OpinionRequest)
        .filter(
            OpinionRequest.case_id == case_id,
            OpinionRequest.status == "sent",
            OpinionRequest.sla_deadline.isnot(None),
            OpinionRequest.sla_deadline < now,
        )
        .all()
    )
    for req in overdue:
        req.status = "no_response"
    if overdue:
        db.commit()
    return len(overdue)
