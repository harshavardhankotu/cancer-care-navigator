"""Immutable case-package snapshots + PDF export via reportlab."""

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from ..config import DISCLAIMER
from ..models import Case, CasePackage, DecisionFlag, Document


def build_snapshot(db: Session, case: Case) -> dict:
    docs = db.query(Document).filter(Document.case_id == case.id).order_by(Document.uploaded_at).all()
    flags = (
        db.query(DecisionFlag)
        .filter(DecisionFlag.case_id == case.id, DecisionFlag.acknowledged.is_(False))
        .all()
    )
    flag_rows = []
    for f in flags:
        row = {"flag_type": f.flag_type, "message": f.message, "triggered_at": f.triggered_at.isoformat()}
        if f.rule:
            row.update({
                "condition": f.rule.condition_description,
                "foreclosed_option": f.rule.foreclosed_option,
                "source_guideline": f.rule.source_guideline,
                "source_citation": f.rule.source_citation,
            })
        flag_rows.append(row)
    return {
        "case": {
            "id": case.id,
            "patient_name": case.patient_name,
            "patient_age": case.patient_age,
            "patient_sex": case.patient_sex,
            "cancer_type": case.cancer_type,
            "stage": case.stage,
            "diagnosis_date": case.diagnosis_date.isoformat() if case.diagnosis_date else None,
            "current_status": case.current_status,
        },
        "documents": [
            {
                "extracted_date": d.extracted_date.isoformat() if d.extracted_date else None,
                "uploaded_at": d.uploaded_at.isoformat(),
                "source": d.extracted_source,
                "doc_type": d.extracted_doc_type,
                "key_findings": d.extracted_key_findings or [],
            }
            for d in docs
        ],
        "open_flags": flag_rows,
        "snapshot_generated_at": datetime.utcnow().isoformat(),
    }


def create_package_version(db: Session, case: Case) -> CasePackage:
    last = (
        db.query(CasePackage)
        .filter(CasePackage.case_id == case.id)
        .order_by(CasePackage.version_number.desc())
        .first()
    )
    version = (last.version_number + 1) if last else 1
    pkg = CasePackage(case_id=case.id, version_number=version, snapshot_json=build_snapshot(db, case))
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def _para(styles, text, style="Normal"):
    return Paragraph(escape(str(text or "")).replace("\n", "<br/>"), styles[style])


def render_case_pdf(snapshot: dict, package_label: str | None = None) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=14 * mm, rightMargin=14 * mm)
    styles = getSampleStyleSheet()
    story = []

    title = "Second-Opinion Case Package"
    if package_label:
        title += f" — {package_label}"
    story.append(_para(styles, title, "Title"))
    story.append(Spacer(1, 4))
    story.append(_para(styles, DISCLAIMER, "Italic"))
    story.append(Spacer(1, 10))

    c = snapshot.get("case", {})
    patient_rows = [
        ["Patient", c.get("patient_name")],
        ["Age / Sex", f"{c.get('patient_age') or '—'} / {c.get('patient_sex') or '—'}"],
        ["Diagnosis", c.get("cancer_type")],
        ["Stage", c.get("stage") or "—"],
        ["Date of diagnosis", c.get("diagnosis_date") or "—"],
        ["Current status", c.get("current_status") or "—"],
    ]
    t = Table([[escape(str(a)), escape(str(b))] for a, b in patient_rows], colWidths=[40 * mm, 130 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(_para(styles, "Patient summary", "Heading2"))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(_para(styles, "Timeline of records", "Heading2"))
    timeline_rows = [["Date", "Source", "Type", "Key findings"]]
    for d in snapshot.get("documents", []):
        timeline_rows.append([
            d.get("extracted_date") or (d.get("uploaded_at") or "")[:10],
            d.get("source") or "—",
            d.get("doc_type") or "—",
            "; ".join(d.get("key_findings") or []) or "—",
        ])
    if len(timeline_rows) == 1:
        timeline_rows.append(["—", "—", "No documents uploaded yet", "—"])
    t2 = Table(timeline_rows, colWidths=[24 * mm, 42 * mm, 40 * mm, 64 * mm])
    t2.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    story.append(_para(styles, "Open questions to raise with your oncologist", "Heading2"))
    flags = snapshot.get("open_flags", [])
    if not flags:
        story.append(_para(styles, "No unacknowledged decision flags at time of generation."))
    for i, f in enumerate(flags, 1):
        if f.get("flag_type") == "coverage_gap":
            story.append(_para(styles, f"{i}. COVERAGE GAP: {f.get('message')}"))
        else:
            story.append(_para(styles, f"{i}. {f.get('condition')}"))
            story.append(_para(styles, f"   Option this may foreclose: {f.get('foreclosed_option')}"))
            story.append(_para(styles, f"   Source: {f.get('source_guideline')} — {f.get('source_citation')}"))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 12))
    story.append(_para(styles, DISCLAIMER, "Italic"))

    doc.build(story)
    return buf.getvalue()
