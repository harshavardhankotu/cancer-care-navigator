"""Focused authorization-scoping tests (pytest).

Run:  python -m pytest tests/ -q
"""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp(suffix='.db')[1]}"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def tokens(client):
    ta = client.post("/api/auth/register", json={"email": "a@t.com", "password": "secretpass1",
                                                 "consent_accepted": True}).json()["token"]
    tb = client.post("/api/auth/register", json={"email": "b@t.com", "password": "secretpass2",
                                                 "consent_accepted": True}).json()["token"]
    return ta, tb


def test_consent_required(client):
    assert client.post("/api/auth/register",
                       json={"email": "c@t.com", "password": "secretpass3"}).status_code == 400


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def test_missing_token_rejected(client):
    assert client.get("/api/cases").status_code == 401


def test_case_scoped_to_owner(client, tokens):
    ta, tb = tokens
    case = client.post("/api/cases", headers=_auth(ta),
                       json={"patient_name": "X", "cancer_type": "breast"}).json()
    cid = case["id"]
    assert client.get(f"/api/cases/{cid}", headers=_auth(tb)).status_code == 404
    assert client.get(f"/api/cases/{cid}", headers=_auth(ta)).status_code == 200
    others = client.get("/api/cases", headers=_auth(tb)).json()
    assert all(c["id"] != cid for c in others)


def test_document_and_package_scoped(client, tokens):
    import io
    ta, tb = tokens
    cid = client.post("/api/cases", headers=_auth(ta),
                      json={"patient_name": "Y", "cancer_type": "colon"}).json()["id"]
    doc = client.post(f"/api/cases/{cid}/documents", headers=_auth(ta),
                      files={"file": ("r.pdf", io.BytesIO(b"%PDF x"), "application/pdf")}).json()
    assert client.get(f"/api/documents/{doc['id']}/file", headers=_auth(tb)).status_code == 404
    pkg = client.post(f"/api/cases/{cid}/packages", headers=_auth(ta)).json()
    assert client.get(f"/api/packages/{pkg['id']}", headers=_auth(tb)).status_code == 404


def test_case_deletion_scoped(client, tokens):
    ta, tb = tokens
    cid = client.post("/api/cases", headers=_auth(ta),
                      json={"patient_name": "Z", "cancer_type": "lung"}).json()["id"]
    # Other user cannot delete
    assert client.delete(f"/api/cases/{cid}", headers=_auth(tb)).status_code == 404
    # Owner can delete
    assert client.delete(f"/api/cases/{cid}", headers=_auth(ta)).status_code == 200
    # Confirm 404 after deletion
    assert client.get(f"/api/cases/{cid}", headers=_auth(ta)).status_code == 404


def test_case_input_validation(client, tokens):
    ta, _ = tokens
    # Empty patient name rejected
    assert client.post("/api/cases", headers=_auth(ta),
                       json={"patient_name": "", "cancer_type": "lung"}).status_code == 422
    # Negative age rejected
    assert client.post("/api/cases", headers=_auth(ta),
                       json={"patient_name": "Test", "cancer_type": "lung", "patient_age": -1}).status_code == 422


def test_security_headers_and_api_404(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    # API 404 returns JSON, not HTML
    unknown = client.get("/api/nonexistent-route-xyz")
    assert unknown.status_code == 404
    assert "application/json" in unknown.headers.get("content-type", "")


def test_storage_path_traversal_protection():
    from app.services.storage import absolute_path
    with pytest.raises(ValueError, match="traversal"):
        absolute_path("../../etc/passwd")
    with pytest.raises(ValueError, match="traversal"):
        absolute_path("..\\..\\windows\\system32")
