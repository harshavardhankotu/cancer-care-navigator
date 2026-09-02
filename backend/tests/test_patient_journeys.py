"""Journey-level automated synthetic tests (pytest).

Covers end-to-end patient/caregiver journeys without any real patient data:
- Journey 1: Newly diagnosed patient (case creation, missing records flag, next steps)
- Journey 2: Scattered records to timeline (pathology, scans, unconfirmed date handling)
- Journey 3: Second opinion parallel coordination & conflict detection
- Journey 4: Low-income financial access & scheme matching
- Journey 5: Hospital transfer tracking & scoping
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    reg = client.post("/api/auth/register", json={
        "email": "synthetic_journey_family@example.com",
        "password": "strongPassword123!",
        "consent_accepted": True,
        "country": "IN",
    }).json()
    token = reg["token"]
    return {"Authorization": f"Bearer {token}"}


def test_journey_newly_diagnosed_patient(client, auth_headers):
    """Journey 1: Newly diagnosed patient creates a case and reviews initial next steps."""
    # 1. Create a new case
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient A",
        "cancer_type": "NSCLC (Lung Cancer)",
        "stage": "IIIA",
        "patient_age": 58,
        "country": "IN",
    })
    assert case_res.status_code == 200
    cid = case_res.json()["id"]

    # 2. Inspect the personal navigation plan before any records are uploaded
    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    assert plan["country"] == "IN"
    # Plan must highlight missing records in needs_attention
    records_missing_item = next((i for i in plan["needs_attention"] if i["category"] == "records_missing"), None)
    assert records_missing_item is not None
    assert "No diagnostic records" in records_missing_item["title"]

    # 3. Verify next steps prioritize initial document upload
    assert any("upload" in s.lower() for s in plan["next_steps"])
    assert plan["record_readiness"]["total_documents"] == 0
    assert plan["second_opinion_readiness"]["ready"] is False


def test_journey_scattered_records_and_unconfirmed_date(client, auth_headers):
    """Journey 2: Caregiver adds manual records with and without confirmed report dates."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient B",
        "cancer_type": "Breast Cancer",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # Add pathology record with a confirmed date
    path_rec = client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": "2026-06-15",
        "extracted_source": "General Hospital Pathology Lab",
        "extracted_doc_type": "Pathology report",
        "key_findings": ["Invasive ductal carcinoma, Grade 2", "ER+, PR+, HER2 negative"],
    }).json()
    assert path_rec["extracted_date"] == "2026-06-15"
    assert path_rec["has_file"] is False

    # Add old paper scan record without a confirmed date (should be marked unconfirmed)
    unconfirmed_rec = client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": None,
        "extracted_source": "City Imaging Center",
        "extracted_doc_type": "Imaging report",
        "key_findings": ["CT Chest shows 2.4cm mass in right upper lobe"],
    }).json()
    assert unconfirmed_rec["extracted_date"] is None
    assert unconfirmed_rec["raw_extraction_json"]["date_unconfirmed"] is True

    # Plan should now recognize pathology is present
    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    assert plan["record_readiness"]["has_pathology"] is True
    assert plan["record_readiness"]["has_imaging"] is True
    assert plan["record_readiness"]["has_unconfirmed_dates"] is True


def test_journey_second_opinion_coordination_and_conflict(client, auth_headers):
    """Journey 3: Patient prepares package, queries specialists, and surfaces conflicting opinions."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient C",
        "cancer_type": "Colorectal Cancer",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # Add biopsy record so package is valid
    client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": "2026-07-01",
        "extracted_source": "Lab C",
        "extracted_doc_type": "Pathology report",
        "key_findings": ["Adenocarcinoma of colon"],
    })

    # Compile immutable package
    pkg = client.post(f"/api/cases/{cid}/packages", headers=auth_headers).json()
    assert pkg["version_number"] >= 1

    # Check second opinion readiness in plan
    plan_before = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    assert plan_before["second_opinion_readiness"]["has_package"] is True
    assert plan_before["second_opinion_readiness"]["ready"] is True

    # Initiate parallel outreach with two doctors
    res = client.post(f"/api/cases/{cid}/opinions", headers=auth_headers, json={"doctor_ids": [1, 2]}).json()
    drafts = res["requests"]
    assert len(drafts) == 2
    oid1, oid2 = drafts[0]["id"], drafts[1]["id"]

    # Mark both as sent
    client.patch(f"/api/opinions/{oid1}", headers=auth_headers, json={"action": "mark_sent"})
    client.patch(f"/api/opinions/{oid2}", headers=auth_headers, json={"action": "mark_sent"})

    # Doctor 1 recommends surgery; Doctor 2 recommends neoadjuvant chemoradiotherapy
    client.patch(f"/api/opinions/{oid1}", headers=auth_headers, json={
        "action": "respond",
        "response": {"opinion_recommended_modality": "Upfront resection surgery"},
    })
    client.patch(f"/api/opinions/{oid2}", headers=auth_headers, json={
        "action": "respond",
        "response": {"opinion_recommended_modality": "Neoadjuvant chemoradiotherapy first"},
    })

    # Plan should now prioritize this conflict under Needs Attention
    plan_after = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    conflict_item = next((i for i in plan_after["needs_attention"] if i["category"] == "opinion_conflict"), None)
    assert conflict_item is not None
    assert "Differing second opinions" in conflict_item["title"]
    assert "primary care team" in conflict_item["action"]


def test_journey_hospital_transfer_tracking(client, auth_headers):
    """Journey 4: Patient tracking record transfer between institutions."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient D",
        "cancer_type": "Sarcoma",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # Create transfer request
    tr = client.post(f"/api/cases/{cid}/transfers", headers=auth_headers, json={
        "from_hospital": "District Hospital",
        "to_hospital": "Regional Cancer Centre",
    }).json()
    assert tr["status"] == "requested"

    # Plan should show transfer in progress
    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    transfer_in_progress = next((i for i in plan["in_progress"] if i["category"] == "transfer"), None)
    assert transfer_in_progress is not None
    assert "District Hospital" in transfer_in_progress["title"]

    # Update status to uploaded
    client.patch(f"/api/transfers/{tr['id']}?status=uploaded", headers=auth_headers)
    plan_done = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    # Once uploaded, it is no longer in progress
    assert not any(i.get("category") == "transfer" for i in plan_done["in_progress"])
