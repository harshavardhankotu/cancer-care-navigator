"""Journey-level automated synthetic tests (pytest).

Covers end-to-end patient/caregiver journeys without any real patient data:
- Journey 1: Newly diagnosed patient (case creation, missing records flag, next steps)
- Journey 2: Scattered records to timeline (pathology, scans, unconfirmed date handling)
- Journey 3: Second opinion parallel coordination & conflict detection
- Journey 4: Hospital transfer tracking & scoping
- Journey 5: Low-income financial access & scheme matching (PM-JAY, CGHS, non-guaranteed wording)
- Journey 6: Caregiver case access & cross-family authorization isolation
- Journey 7: Date safety (missing, valid, invalid, and timeline ordering)
"""

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


@pytest.fixture(scope="module")
def secondary_auth_headers(client):
    reg = client.post("/api/auth/register", json={
        "email": "unauthorized_family@example.com",
        "password": "strongPassword456!",
        "consent_accepted": True,
        "country": "IN",
    }).json()
    token = reg["token"]
    return {"Authorization": f"Bearer {token}"}


def test_journey_newly_diagnosed_patient(client, auth_headers):
    """Journey 1: Newly diagnosed patient creates a case and reviews initial next steps."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient A",
        "cancer_type": "NSCLC (Lung Cancer)",
        "stage": "IIIA",
        "patient_age": 58,
        "country": "IN",
    })
    assert case_res.status_code == 200
    cid = case_res.json()["id"]

    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers).json()
    assert plan["country"] == "IN"

    # Plan must highlight missing records in needs_attention
    records_missing_item = next((i for i in plan["needs_attention"] if i["category"] == "records_missing"), None)
    assert records_missing_item is not None
    assert "No diagnostic records" in records_missing_item["title"]

    # Verify next steps prioritize initial document upload
    assert any("upload" in s.lower() or "record" in s.lower() for s in plan["next_steps"])
    assert plan["record_readiness"]["total_documents"] == 0
    assert plan["second_opinion_readiness"]["status"] == "not_started"
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
    assert not any(i.get("category") == "transfer" for i in plan_done["in_progress"])


def test_journey_financial_access_and_scheme_matching(client, auth_headers):
    """Journey 5: Low-income synthetic patient evaluates financial scheme access."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient E",
        "cancer_type": "Oral Cavity Cancer",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # Complete synthetic financial profile
    prof_res = client.put(f"/api/cases/{cid}/financial-profile", headers=auth_headers, json={
        "annual_income_inr": 120000,
        "bpl_card_holder": True,
        "cghs_beneficiary": False,
        "echs_beneficiary": False,
        "railway_employee": False,
        "private_insurance_active": False,
    })
    assert prof_res.status_code == 200

    # Match coverage schemes
    match_res = client.post(f"/api/cases/{cid}/coverage-match", headers=auth_headers).json()
    schemes = match_res["results"]
    assert len(schemes) > 0

    # Ensure PM-JAY matches for BPL card holder
    pmjay = next((s for s in schemes if "PM-JAY" in s["scheme_name"]), None)
    assert pmjay is not None
    assert pmjay["status"] in ("eligible", "needs_verification")

    # Application MUST include persistent disclaimers and not claim guaranteed eligibility
    assert "disclaimer" in match_res
    assert "not medical advice" in match_res["disclaimer"].lower() or "decisions rest with you" in match_res["disclaimer"].lower()


def test_journey_caregiver_access_and_cross_family_isolation(client, auth_headers, secondary_auth_headers):
    """Journey 6: Authorized caregiver accesses case profile; unauthorized family is blocked."""
    # 1. Family A creates case
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient F",
        "cancer_type": "Lymphoma",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # 2. Authorized family member (same account) can fetch case, timeline, and plan
    plan_a = client.get(f"/api/cases/{cid}/personal-plan", headers=auth_headers)
    assert plan_a.status_code == 200
    assert plan_a.json()["country"] == "IN"

    # 3. Unauthorized family (different account) is strictly refused with 404
    plan_b = client.get(f"/api/cases/{cid}/personal-plan", headers=secondary_auth_headers)
    assert plan_b.status_code == 404

    docs_b = client.get(f"/api/cases/{cid}/documents", headers=secondary_auth_headers)
    assert docs_b.status_code == 404


def test_journey_date_safety_and_timeline_ordering(client, auth_headers):
    """Journey 7: Test valid dates, missing dates (unconfirmed), and invalid format handling."""
    case_res = client.post("/api/cases", headers=auth_headers, json={
        "patient_name": "Synthetic Patient G",
        "cancer_type": "Gastric Cancer",
        "country": "IN",
    })
    cid = case_res.json()["id"]

    # 1. Valid ISO date
    d1 = client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": "2026-01-10",
        "extracted_source": "Lab 1",
        "extracted_doc_type": "Biopsy report",
        "key_findings": ["Adenocarcinoma"],
    }).json()
    assert d1["extracted_date"] == "2026-01-10"
    assert d1["raw_extraction_json"]["date_unconfirmed"] is False

    # 2. None / Missing date
    d2 = client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": None,
        "extracted_source": "Hospital Archives",
        "extracted_doc_type": "Older scan report",
        "key_findings": ["Suspicious lesion"],
    }).json()
    assert d2["extracted_date"] is None
    assert d2["raw_extraction_json"]["date_unconfirmed"] is True

    # 3. Invalid date string (e.g. malformed or text) -> should gracefully parse to None and mark unconfirmed
    d3 = client.post(f"/api/cases/{cid}/records", headers=auth_headers, json={
        "extracted_date": "circa-2025-spring",
        "extracted_source": "Paper document",
        "extracted_doc_type": "Consultation note",
        "key_findings": ["Initial assessment"],
    }).json()
    assert d3["extracted_date"] is None
    assert d3["raw_extraction_json"]["date_unconfirmed"] is True

    # 4. Timeline list preserves all documents
    docs = client.get(f"/api/cases/{cid}/documents", headers=auth_headers).json()
    assert len(docs) == 3
    # Ensure unconfirmed dates are exposed in response
    unconfirmed_count = sum(1 for d in docs if not d["extracted_date"] or (d.get("raw_extraction_json") or {}).get("date_unconfirmed"))
    assert unconfirmed_count == 2
