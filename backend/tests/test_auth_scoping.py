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
    ta = client.post("/api/auth/register", json={"email": "a@t.com", "password": "secret1"}).json()["token"]
    tb = client.post("/api/auth/register", json={"email": "b@t.com", "password": "secret2"}).json()["token"]
    return ta, tb


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
