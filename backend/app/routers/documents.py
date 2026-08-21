from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_family, owned_case
from ..config import STORAGE_DIR
from ..database import get_db
from ..models import Document, Family
from ..schemas import DocumentOut, DocumentPatch
from ..services.extraction import extract_document
from ..services.rules_engine import evaluate_case
from ..services import storage
from ..services.storage import absolute_path, delete_file, save_file

router = APIRouter(prefix="/api", tags=["documents"])


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


class ManualRecord(BaseModel):
    extracted_date: str | None = None
    extracted_source: str | None = None
    extracted_doc_type: str | None = None
    key_findings: list[str] | None = None


@router.post("/cases/{case_id}/records", response_model=DocumentOut)
def add_manual_record(case_id: int, body: ManualRecord, db: Session = Depends(get_db),
                      family: Family = Depends(get_current_family)):
    """Add a timeline entry WITHOUT uploading a file — fastest path for paper-era records."""
    case = owned_case(db, family, case_id)
    if not any([body.extracted_date, body.extracted_source, body.extracted_doc_type,
                body.key_findings]):
        raise HTTPException(status_code=400, detail="Enter at least one field")
    doc = Document(
        case_id=case.id,
        file_path=None,
        extracted_date=_parse_date(body.extracted_date) or date.today(),
        extracted_source=body.extracted_source or "Not recorded",
        extracted_doc_type=body.extracted_doc_type or "Note / record",
        extracted_key_findings=[f for f in (body.key_findings or []) if f.strip()],
        raw_extraction_json={"ocr_engine": "manual", "extraction_mode": "manual"},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    evaluate_case(db, case)
    return doc


@router.post("/cases/{case_id}/documents", response_model=DocumentOut)
def upload_document(case_id: int, request: Request, file: UploadFile = File(...),
                    extracted_date: str | None = Form(None),
                    extracted_source: str | None = Form(None),
                    extracted_doc_type: str | None = Form(None),
                    db: Session = Depends(get_db), family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)

    # Reject oversized uploads BEFORE buffering them into memory.
    clen = request.headers.get("content-length")
    if clen and clen.isdigit() and int(clen) > storage.MAX_UPLOAD_BYTES + 64 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit.")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = file.file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > storage.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds 25 MB limit.")
        chunks.append(chunk)
    content = b"".join(chunks)
    try:
        rel_path = save_file(family.id, case.id, file.filename or "upload", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    extraction = extract_document(rel_path, file.filename or "", storage_dir=STORAGE_DIR)
    doc = Document(
        case_id=case.id,
        file_path=rel_path,
        original_filename=file.filename,
        extracted_date=_parse_date(extracted_date) or _parse_date(extraction["extracted_date"]),
        extracted_source=extracted_source or extraction["extracted_source"],
        extracted_doc_type=extracted_doc_type or extraction["extracted_doc_type"],
        extracted_key_findings=extraction["extracted_key_findings"],
        raw_extraction_json=extraction["raw_extraction_json"],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    evaluate_case(db, case)
    return doc


@router.get("/cases/{case_id}/documents", response_model=list[DocumentOut])
def list_documents(case_id: int, db: Session = Depends(get_db),
                   family: Family = Depends(get_current_family)):
    case = owned_case(db, family, case_id)
    return (db.query(Document).filter(Document.case_id == case.id)
            .order_by(Document.uploaded_at.desc()).all())


@router.patch("/documents/{doc_id}", response_model=DocumentOut)
def correct_extraction(doc_id: int, body: DocumentPatch, db: Session = Depends(get_db),
                       family: Family = Depends(get_current_family)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    owned_case(db, family, doc.case_id)
    updates = body.model_dump(exclude_unset=True)
    if "extracted_date" in updates:
        updates["extracted_date"] = _parse_date(updates["extracted_date"])
    for field, value in updates.items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    evaluate_case(db, doc.case)
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db),
                    family: Family = Depends(get_current_family)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    owned_case(db, family, doc.case_id)
    if doc.file_path:
        delete_file(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.get("/documents/{doc_id}/file")
def download_document(doc_id: int, db: Session = Depends(get_db),
                      family: Family = Depends(get_current_family)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    owned_case(db, family, doc.case_id)
    if not doc.file_path:
        raise HTTPException(status_code=404, detail="This record has no attached file")
    path = absolute_path(doc.file_path)
    import os
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(path, filename=doc.original_filename or "document")
