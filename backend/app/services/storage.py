"""Local filesystem storage under STORAGE_DIR.

Layout: <STORAGE_DIR>/<family_id>/<case_id>/<uuid>_<filename>
This mirrors an S3-style key structure so it can be swapped for S3-compatible
storage later by re-implementing save_file/delete_file only. Files are never
stored in the database as blobs.
"""

import os
import re
import uuid

from ..config import STORAGE_DIR

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def save_file(family_id: int, case_id: int, filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type {ext!r}. Allowed: PDF, PNG, JPG.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds 25 MB limit.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(filename))[:120] or "upload"
    rel_path = os.path.join(str(family_id), str(case_id), f"{uuid.uuid4().hex[:8]}_{safe_name}")
    abs_path = os.path.join(STORAGE_DIR, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as fh:
        fh.write(content)
    return rel_path


def delete_file(rel_path: str) -> None:
    try:
        abs_path = absolute_path(rel_path)
    except ValueError:
        return
    if os.path.isfile(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass


def absolute_path(rel_path: str) -> str:
    base = os.path.abspath(STORAGE_DIR)
    target = os.path.abspath(os.path.join(base, rel_path))
    if not target.startswith(base):
        raise ValueError("Invalid storage path traversal attempt")
    return target
