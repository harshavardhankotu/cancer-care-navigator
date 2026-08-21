"""Foreclosure rules engine.

Heuristic keyword matcher over case fields + extracted document text. Each rule
is keyed by ForeclosureRule.id and evaluated against a context dict:

    ctx = {
        "cancer_type": str (lower), "stage": str (lower),
        "current_status": str (lower), "patient_age": int|None,
        "doc_types": set[str] (lower), "findings": str (all findings joined, lower),
        "sources": set[str] (lower),
    }

IMPORTANT: these predicates are MVP heuristics written to accompany real,
citable guideline summaries in seed data. A clinician must review both the
rule text and these match conditions before production use.
"""

import re

from sqlalchemy.orm import Session

from ..models import Case, DecisionFlag, Document, ForeclosureRule


def build_context(db: Session, case: Case) -> dict:
    docs = db.query(Document).filter(Document.case_id == case.id).all()
    doc_types = {(d.extracted_doc_type or "").lower() for d in docs}
    sources = {(d.extracted_source or "").lower() for d in docs}
    findings = " ".join(
        " ".join(d.extracted_key_findings or []).lower() for d in docs
    )
    blob = " ".join(doc_types) + " " + findings
    return {
        "cancer_type": (case.cancer_type or "").lower(),
        "stage": (case.stage or "").lower(),
        "current_status": (case.current_status or "").lower(),
        "patient_age": case.patient_age,
        "doc_types": doc_types,
        "sources": sources,
        "findings": findings,
        "blob": blob,
    }


def _has(text: str, *keywords: str) -> bool:
    return any(k in text for k in keywords)


def _is_nsclc(cancer_type: str) -> bool:
    return ("lung" in cancer_type
            and "sclc" not in cancer_type
            and not re.search(r"(?<!non-)small cell", cancer_type))


RULE_PREDICATES = {
    # 1. Steroids before lymphoma biopsy
    1: lambda c: (
        _has(c["cancer_type"], "lymphoma", "hodgkin")
        and _has(c["current_status"], "steroid", "predniso", "dexamethasone")
        and not any("pathology" in t for t in c["doc_types"])
    ),
    # 2. NSCLC definitive radiation before biomarker testing
    2: lambda c: (
        _is_nsclc(c["cancer_type"])
        and _has(c["current_status"], "radiation", "radiotherapy", "chemoradiation", "concurrent chemo")
        and not any(k in c["blob"] for k in ("egfr", "alk ", "alk+", "ros1", "biomarker", "molecular", "mutation"))
    ),
    # 3. Soft-tissue sarcoma biopsy outside specialist centre / unplanned excision
    3: lambda c: (
        _has(c["cancer_type"], "sarcoma")
        and _has(c["current_status"], "biopsy", "excision")
        and _has(c["current_status"], "outside", "referring", "local hospital", "enucleation", "whoops")
    ),
    # 4. Primary bone tumour biopsy at non-oncology centre
    4: lambda c: (
        _has(c["cancer_type"], "osteosarcoma", "ewing", "bone tumor", "bone tumour")
        and _has(c["current_status"], "biopsy")
        and not any(
            k in s for s in c["sources"]
            for k in ("cancer institute", "tata", "aiims", "regional cancer", "oncology centre", "oncology center")
        )
    ),
    # 5. Gonadotoxic therapy without fertility-preservation counselling (age <= 45)
    5: lambda c: (
        c["patient_age"] is not None
        and c["patient_age"] <= 45
        and _has(c["current_status"], "chemotherapy", "chemo", "radiation", "radiotherapy")
        and not any(k in c["blob"] for k in ("fertility", "sperm", "oocyte", "embryo", "gonad"))
    ),
    # 6. Up-front surgery in locally advanced / TNBC / HER2+ stage II-III breast cancer
    6: lambda c: (
        _has(c["cancer_type"], "breast")
        and bool(c["stage"])
        and ("ii" in c["stage"] or "iii" in c["stage"])
        and _has(c["current_status"], "surgery first", "upfront surgery", "up-front surgery",
                 "mrm", "mastectomy scheduled", "planned surgery first")
    ),
    # 7. Anti-EGFR before RAS testing in metastatic colorectal cancer
    7: lambda c: (
        _has(c["cancer_type"], "colorectal", "colon", "rectal")
        and (_has(c["cancer_type"] + " " + c["stage"], "metastatic", "stage iv"))
        and _has(c["current_status"], "cetuximab", "panitumumab")
        and not any(k in c["blob"] for k in ("ras", "kras", "nras"))
    ),
    # 8. Radiation-only local therapy in operable early oral cavity/larynx cancer
    8: lambda c: (
        _has(c["cancer_type"], "oral", "larynx", "laryngeal", "oropharyn", "mouth", "tongue")
        and _has(c["current_status"], "radiation only", "radiotherapy only", "rt alone", "radiation as sole")
        and "surgery" not in c["current_status"]
    ),
}


def evaluate_case(db: Session, case: Case) -> list[DecisionFlag]:
    """Create decision_flags rows for newly-matching rules; dedupe open flags."""
    ctx = build_context(db, case)
    created = []
    rules = db.query(ForeclosureRule).filter(ForeclosureRule.id.in_(RULE_PREDICATES.keys())).all()
    open_rule_ids = {
        f.foreclosure_rule_id
        for f in db.query(DecisionFlag)
        .filter(DecisionFlag.case_id == case.id, DecisionFlag.flag_type == "foreclosure",
                DecisionFlag.acknowledged.is_(False))
        .all()
    }
    for rule in rules:
        predicate = RULE_PREDICATES.get(rule.id)
        if predicate is None or rule.id in open_rule_ids:
            continue
        try:
            matched = predicate(ctx)
        except Exception:
            matched = False
        if matched:
            flag = DecisionFlag(case_id=case.id, foreclosure_rule_id=rule.id, flag_type="foreclosure")
            db.add(flag)
            created.append(flag)
    if created:
        db.commit()
    return created
