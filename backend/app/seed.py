"""Idempotent seeding: inserts seed rows only if the tables are empty.

Run manually:  python -m app.seed
Also runs automatically on app startup.
"""

from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .models import (CoverageScheme, Doctor, ForeclosureRule,
                     PatientAssistanceProgram, SpecialistCenter, Trial)
from .seed_data import (COVERAGE_SCHEMES, DOCTORS, FORECLOSURE_RULES,
                        PATIENT_ASSISTANCE_PROGRAMS, SPECIALIST_CENTERS, TRIALS)


def _seed(db: Session) -> None:
    if db.query(ForeclosureRule).count() == 0:
        for r in FORECLOSURE_RULES:
            db.add(ForeclosureRule(**r))
    if db.query(SpecialistCenter).count() == 0:
        for c in SPECIALIST_CENTERS:
            c = dict(c)
            c["verified_by"] = "seed-starter-list (requires manual verification)"
            from datetime import date
            c["last_verified_date"] = date.today()
            db.add(SpecialistCenter(**c))
    if db.query(Doctor).count() == 0:
        for d in DOCTORS:
            d = dict(d)
            d["verified_by"] = "PLACEHOLDER - not a real individual"
            from datetime import date
            d["last_verified_date"] = date.today()
            db.add(Doctor(**d))
    if db.query(Trial).count() == 0:
        for t in TRIALS:
            db.add(Trial(**t))
    if db.query(CoverageScheme).count() == 0:
        for s in COVERAGE_SCHEMES:
            db.add(CoverageScheme(**s))
    if db.query(PatientAssistanceProgram).count() == 0:
        for p in PATIENT_ASSISTANCE_PROGRAMS:
            db.add(PatientAssistanceProgram(**p))
    db.commit()


def _seed_demo(db: Session) -> None:
    """Idempotent demo account so evaluators can click 'Try demo' and see a populated app."""
    from datetime import date, datetime, timedelta

    from .auth import hash_password
    from .models import (Case, CasePackage, DecisionFlag, Doctor, Document,
                         Family, OpinionRequest)
    from .services.packages import create_package_version

    if db.query(Family).filter(Family.email == "demo@navigator.app").first():
        return
    fam = Family(email="demo@navigator.app", password_hash=hash_password("demo1234"))
    db.add(fam)
    db.commit()
    db.refresh(fam)

    case = Case(
        family_id=fam.id, patient_name="Ramesh Kumar (demo)", patient_age=58,
        patient_sex="male", cancer_type="Non-small cell lung cancer", stage="IIIB",
        diagnosis_date=date.today() - timedelta(days=45),
        current_status="Concurrent chemoradiation started at district hospital; "
                       "biomarker test results not yet received",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    docs = [
        Document(case_id=case.id, file_path=None,
                 extracted_date=date.today() - timedelta(days=45),
                 extracted_source="District Government Hospital",
                 extracted_doc_type="Pathology report",
                 extracted_key_findings=["Adenocarcinoma, lung primary (demo entry)"],
                 raw_extraction_json={"extraction_mode": "manual", "ocr_engine": "manual"}),
        Document(case_id=case.id, file_path=None,
                 extracted_date=date.today() - timedelta(days=20),
                 extracted_source="District Government Hospital",
                 extracted_doc_type="Imaging report (CT/MRI)",
                 extracted_key_findings=["Locally advanced disease, Stage IIIB (demo entry)"],
                 raw_extraction_json={"extraction_mode": "manual", "ocr_engine": "manual"}),
        Document(case_id=case.id, file_path=None,
                 extracted_date=date.today() - timedelta(days=10),
                 extracted_source="District Government Hospital",
                 extracted_doc_type="Prescription / treatment plan",
                 extracted_key_findings=["Concurrent chemoradiation started (demo entry)"],
                 raw_extraction_json={"extraction_mode": "manual", "ocr_engine": "manual"}),
    ]
    db.add_all(docs)

    pkg = create_package_version(db, case)
    from .seed_data import DOCTORS
    doctor_rows = []
    for i, d in enumerate(DOCTORS[:2]):
        row = Doctor(**{**d, "verified_by": "PLACEHOLDER - not a real individual",
                        "last_verified_date": date.today()})
        db.add(row)
        doctor_rows.append(row)
    db.commit()
    for row in doctor_rows:
        db.refresh(row)

    now = datetime.utcnow()
    reqs = [
        OpinionRequest(case_id=case.id, doctor_id=doctor_rows[0].id,
                       status="opinion_received",
                       case_package_version_id=pkg.id, sent_at=now - timedelta(days=9),
                       sla_deadline=now + timedelta(days=2), responded_at=now - timedelta(days=3),
                       opinion_recommended_modality="Continue chemoradiation, then reassess",
                       opinion_sequencing_note="Complete planned course; repeat imaging after (demo)",
                       opinion_caveats="Demo placeholder content",
                       conflicts_flagged=True),
        OpinionRequest(case_id=case.id, doctor_id=doctor_rows[1].id,
                       status="opinion_received",
                       case_package_version_id=pkg.id, sent_at=now - timedelta(days=8),
                       sla_deadline=now + timedelta(days=3), responded_at=now - timedelta(days=1),
                       opinion_recommended_modality="Pause RT until EGFR/ALK results return",
                       opinion_sequencing_note="Biomarker-first sequencing may change therapy class (demo)",
                       opinion_caveats="Demo placeholder content",
                       conflicts_flagged=True),
    ]
    db.add_all(reqs)
    db.commit()


def seed_if_empty(db: Session | None = None) -> None:
    own = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        own = True
    try:
        _seed(db)
        _seed_demo(db)
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    seed_if_empty()
    print("Seed complete (idempotent — existing rows untouched).")