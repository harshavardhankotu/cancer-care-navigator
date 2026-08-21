"""Document-extraction interface.

ZERO-COST pipeline, two modes:
1. "pdf_text" — digital PDFs: extracts the embedded text layer with pypdf (free,
   pure Python), then pulls out dates, a guessed document type and source.
2. "stub" — scanned/image files or unreadable PDFs fall back to clearly-marked
   placeholder fields that the family corrects manually. The UI always shows
   which mode produced the entry, and manual correction is one click.

To go beyond zero cost later, swap this function for a cloud OCR API — nothing
else changes; the returned dict shape is the contract:

    extract_document(file_path, original_filename) -> {
      extracted_date (ISO date|None), extracted_source, extracted_doc_type,
      extracted_key_findings (list[str]), raw_extraction_json (dict)
    }
"""

import hashlib
import os
import re
from datetime import date, timedelta

DOC_TYPE_KEYWORDS = [
    (("pathology", "biopsy", "histopath", "ihn", "ihc"), "Pathology report"),
    (("discharge", "summary of care"), "Discharge summary"),
    (("mri", "ct scan", "ct ", "pet ", "x-ray", "xray", "ultrasound", "sonography"), "Imaging report"),
    (("prescription", "rx", "treatment plan", "chemotherapy cycle"), "Prescription / treatment plan"),
    (("hemogram", "blood", "cbc", "biomarker", "tumour marker", "tumor marker", "lab"), "Lab report"),
]
SOURCE_KEYWORDS = ("hospital", "centre", "center", "institute", "clinic", "laboratory", "labs", "diagnostic")
DATE_PATTERNS = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b([0-3]?\d[/\-.][0-1]?\d[/\-.](?:20)?\d{2})\b"),
]
FINDINGS_HINTS = re.compile(
    r"(?:finding|impression|diagnosis|conclusion|result|stage|grade|margin|metastasis|"
    r"carcinoma|adenocarcinoma|lymphoma|sarcoma|tumor|tumour)[^\n]{10,200}",
    re.IGNORECASE,
)


def _stub(file_path: str, original_filename: str) -> dict:
    h = int(hashlib.md5((original_filename or file_path).encode()).hexdigest(), 16)
    doc_type = ["Pathology report", "Imaging report (CT/MRI)", "Discharge summary",
                "Lab report", "Prescription / treatment plan"][h % 5]
    return {
        "extracted_date": None,
        "extracted_source": "Unknown hospital/lab (please correct)",
        "extracted_doc_type": doc_type,
        "extracted_key_findings": [
            "[PLACEHOLDER EXTRACTION] No readable text layer found (scanned file?).",
            "Please correct date, source and findings below — takes ~30 seconds.",
        ],
        "raw_extraction_json": {
            "ocr_engine": "stub",
            "extraction_mode": "stub",
            "note": "No OCR performed. Free local pipeline could not read text.",
            "file_path": file_path,
        },
    }


def _extract_pdf_text(abs_path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(abs_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages[:6])
    except Exception:
        return ""


def _guess_doc_type(text_lower: str) -> str | None:
    for keywords, label in DOC_TYPE_KEYWORDS:
        if any(k in text_lower for k in keywords):
            return label
    return None


def _guess_source(text_lower: str) -> str | None:
    for line in text_lower.splitlines():
        if any(k in line for k in SOURCE_KEYWORDS) and len(line.strip()) > 4:
            candidate = line.strip()[:120]
            return candidate.title()[:120]
    return None


def _guess_date(text: str) -> str | None:
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        raw = m.group(1)
        try:
            parts = re.split(r"[/\-.]", raw)
            if len(parts[0]) == 4:
                d = date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                year = int(parts[2])
                year = year + 2000 if year < 100 else year
                d = date(year, int(parts[1]), int(parts[0]))
            return d.isoformat()
        except (ValueError, IndexError):
            continue
    return None


def extract_document(file_path: str, original_filename: str = "", storage_dir: str | None = None) -> dict:
    ext = os.path.splitext(original_filename or file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        abs_path = os.path.join(storage_dir, file_path) if storage_dir else file_path
        text = _extract_pdf_text(abs_path)

    if len(text.strip()) < 40:
        return _stub(file_path, original_filename)

    text_lower = text.lower()
    matches = [m.group(0).strip()[:250] for m in FINDINGS_HINTS.finditer(text)][:5]
    key_findings = matches or [text.strip()[:300]]
    guessed_date = _guess_date(text)
    return {
        "extracted_date": guessed_date,
        "extracted_source": _guess_source(text_lower) or "Unknown hospital/lab (please correct)",
        "extracted_doc_type": _guess_doc_type(text_lower) or "Report",
        "extracted_key_findings": key_findings,
        "raw_extraction_json": {
            "ocr_engine": "pypdf-text-layer",
            "extraction_mode": "pdf_text",
            "chars_extracted": len(text),
            "note": "Auto-extracted from the PDF text layer at zero cost. Verify fields before relying on them.",
            "file_path": file_path,
        },
    }
