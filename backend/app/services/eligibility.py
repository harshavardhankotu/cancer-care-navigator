"""Rules-based coverage-scheme eligibility matching.

No real insurance/eligibility APIs are called. Schemes carry structured
`eligibility_criteria_json` (curated by an insurance analyst; see seed data)
with simple check objects:

    {"field": "<profile field>", "op": "<op>", "value": [...]}

Ops:
  in            -> profile value must be one of `value`; missing => unknown
  not_in        -> profile value must NOT be in `value`; missing => pass
  in_or_unknown -> like `in`, but missing profile field passes as unknown

Aggregate result per scheme: eligible | not_eligible | needs_verification.
"""

from sqlalchemy.orm import Session

from ..models import Case, CaseFinancialProfile, CoverageScheme, OpinionRequest, TransferRequest

PROFILE_FIELDS = ("insurance_status", "insurer_name", "income_bracket", "budget_ceiling")


def evaluate_scheme(scheme: CoverageScheme, profile: dict) -> dict:
    criteria = scheme.eligibility_criteria_json or {}
    checks = criteria.get("checks", [])
    reasons = []
    unknown = False
    failed = False
    for check in checks:
        field = check.get("field")
        op = check.get("op")
        allowed = [str(v).lower() for v in check.get("value", [])]
        actual = profile.get(field)
        actual_l = str(actual).lower() if actual is not None else None
        if op == "in":
            if actual_l is None:
                unknown = True
                reasons.append(f"{field}: not provided — verify against scheme rules")
            elif actual_l not in allowed:
                failed = True
                reasons.append(f"{field} '{actual}' does not match scheme criteria")
            else:
                reasons.append(f"{field} '{actual}' matches scheme criteria")
        elif op == "not_in":
            if actual_l is not None and actual_l in allowed:
                failed = True
                reasons.append(f"{field} '{actual}' is excluded by this scheme's criteria")
        elif op == "in_or_unknown":
            if actual_l is None:
                unknown = True
                reasons.append(f"{field}: not provided — verify against scheme rules")
            elif actual_l not in allowed:
                failed = True
                reasons.append(f"{field} '{actual}' does not match scheme criteria")
            else:
                reasons.append(f"{field} '{actual}' matches scheme criteria")
    if failed:
        status = "not_eligible"
    elif unknown:
        status = "needs_verification"
    else:
        status = "eligible"
    return {
        "scheme_id": scheme.id,
        "scheme_name": scheme.scheme_name,
        "status": status,
        "reasons": reasons,
        "coverage_limit": scheme.coverage_limit,
        "covered_treatments": scheme.covered_treatments or [],
        "exclusions": scheme.exclusions or [],
    }


def case_hospitals(db: Session, case: Case) -> list[str]:
    hospitals = []
    opinions = db.query(OpinionRequest).filter(OpinionRequest.case_id == case.id).all()
    for o in opinions:
        if o.doctor and o.doctor.hospital:
            hospitals.append(o.doctor.hospital)
    transfers = db.query(TransferRequest).filter(TransferRequest.case_id == case.id).all()
    for t in transfers:
        for h in (t.from_hospital, t.to_hospital):
            if h:
                hospitals.append(h)
    return list(dict.fromkeys(hospitals))


def network_matches(db: Session, case: Case) -> list[dict]:
    """Flag which schemes' network hospital lists overlap this case's hospitals."""
    hospitals = case_hospitals(db, case)
    results = []
    for scheme in db.query(CoverageScheme).all():
        network = [n.lower() for n in (scheme.network_hospitals or [])]
        hits = [h for h in hospitals if any(h.lower() in n or n in h.lower() for n in network)]
        if hits:
            results.append({"scheme_name": scheme.scheme_name, "matched_hospitals": hits})
    return results


def run_case_match(db: Session, case: Case) -> dict:
    prof_row = db.query(CaseFinancialProfile).filter(CaseFinancialProfile.case_id == case.id).first()
    profile = {f: getattr(prof_row, f) for f in PROFILE_FIELDS} if prof_row else {}
    results = [evaluate_scheme(s, profile) for s in db.query(CoverageScheme).all()]
    eligible = [r for r in results if r["status"] == "eligible"]
    gaps = []
    insurance_status = (profile.get("insurance_status") or "").lower()
    if insurance_status == "uninsured" and not eligible:
        gaps.append(
            "No insurance recorded and no public scheme clearly matched this profile. "
            "Check PM-JAY beneficiary lists at an empanelled hospital Ayushman desk."
        )
    matches = network_matches(db, case)
    hospitals = case_hospitals(db, case)
    if eligible and not matches and hospitals:
        gaps.append(
            "An eligible scheme was found, but none of the hospitals involved in this case "
            f"({', '.join(hospitals)}) appear on its seeded network list. Verify empanelment "
            "before assuming cashless treatment there."
        )
    return {"results": results, "network_matches": matches, "gaps": gaps}
