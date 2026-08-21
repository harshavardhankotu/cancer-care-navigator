"""End-to-end smoke test using FastAPI TestClient (no server needed).

Run:  python smoke_test.py   (from backend/, inside the venv)
Exercises: auth scoping, case CRUD, document upload + OCR stub, foreclosure
rules engine, packages (immutable snapshots) + PDF, doctor outreach state
machine + SLA + conflict detection, centers/wait-times/transfers, trials,
financial profile + coverage matching, public coverage check.
"""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PASS = 0


def check(name, cond):
    global PASS
    assert cond, f"FAILED: {name}"
    PASS += 1
    print(f"  ok - {name}")


def auth(tok):
    return {"Authorization": f"Bearer {tok}"}


with client:
    print("== health ==")
    r = client.get("/api/health")
    check("health", r.status_code == 200)

    print("== auth & scoping ==")
    check("register WITHOUT consent rejected (DPDP)",
          client.post("/api/auth/register",
                      json={"email": "no-consent@test.com", "password": "secret1"}).status_code == 400)
    tok_a = client.post("/api/auth/register", json={"email": "fam-a@test.com", "password": "secret1",
                                                    "consent_accepted": True}).json()["token"]
    tok_b = client.post("/api/auth/register", json={"email": "fam-b@test.com", "password": "secret2",
                                                    "consent_accepted": True}).json()["token"]
    check("register two families", bool(tok_a) and bool(tok_b))
    check("no token -> 401", client.get("/api/cases").status_code == 401)
    check("bad login -> 401",
          client.post("/api/auth/login", json={"email": "fam-a@test.com", "password": "wrong"}).status_code == 401)

    case = client.post("/api/cases", headers=auth(tok_a), json={
        "patient_name": "Test Patient", "cancer_type": "Non-small cell lung cancer",
        "patient_age": 58, "patient_sex": "male", "stage": "IIIB",
        "current_status": "Concurrent chemoradiation started at local hospital",
    }).json()
    cid = case["id"]
    check("create case", case["cancer_type"].startswith("Non-small"))
    check("other family cannot read case -> 404",
          client.get(f"/api/cases/{cid}", headers=auth(tok_b)).status_code == 404)
    check("case list scoped to family",
          all(c["id"] != cid for c in client.get("/api/cases", headers=auth(tok_b)).json()))

    print("== feature 1: documents + timeline ==")
    pdf_bytes = b"%PDF-1.4 fake pdf content"
    r = client.post(f"/api/cases/{cid}/documents", headers=auth(tok_a),
                    files={"file": ("ct-report.pdf", io.BytesIO(pdf_bytes), "application/pdf")})
    check("upload document", r.status_code == 200)
    doc = r.json()
    check("OCR stub marked stubbed", doc["raw_extraction_json"]["ocr_engine"] == "stub")
    check("other family cannot fetch file -> 404",
          client.get(f"/api/documents/{doc['id']}/file", headers=auth(tok_b)).status_code == 404)
    docs = client.get(f"/api/cases/{cid}/documents", headers=auth(tok_a)).json()
    check("document listed", len(docs) == 1)

    print("== feature 2: foreclosure flags ==")
    flags = client.get(f"/api/cases/{cid}/flags", headers=auth(tok_a)).json()
    rule_flags = [f for f in flags if f["flag_type"] == "foreclosure" and f["rule"]]
    check("NSCLC radiation-before-biomarker flag fired", len(rule_flags) >= 1)
    check("flag carries citation", "NCCN" in rule_flags[0]["rule"]["source_citation"])
    fid = rule_flags[0]["id"]
    check("other family cannot acknowledge -> 404",
          client.post(f"/api/cases/flags/{fid}/acknowledge", headers=auth(tok_b)).status_code == 404)
    client.post(f"/api/cases/flags/{fid}/acknowledge", headers=auth(tok_a))
    flags_after = [f for f in client.get(f"/api/cases/{cid}/flags", headers=auth(tok_a)).json()
                   if not f["acknowledged"]]
    check("acknowledge works", len(flags_after) == 0)

    print("== feature 3+5: packages + PDF export ==")
    p1 = client.post(f"/api/cases/{cid}/packages", headers=auth(tok_a)).json()
    p2 = client.post(f"/api/cases/{cid}/packages", headers=auth(tok_a)).json()
    check("package versions increment", p2["version_number"] == p1["version_number"] + 1)
    snap1 = client.get(f"/api/packages/{p1['id']}", headers=auth(tok_a)).json()["snapshot_json"]
    check("snapshot immutable content present", snap1["case"]["patient_name"] == "Test Patient")
    check("no update route on package (immutability)",
          client.patch(f"/api/packages/{p1['id']}", json={}, headers=auth(tok_a)).status_code == 405)
    pdf = client.get(f"/api/packages/{p2['id']}/pdf", headers=auth(tok_a))
    check("PDF downloads", pdf.status_code == 200 and pdf.content[:4] == b"%PDF")

    print("== feature 5: doctor outreach ==")
    doctors = client.get("/api/doctors", headers=auth(tok_a)).json()
    check("doctors seeded as placeholders",
          len(doctors) >= 3 and "PLACEHOLDER" in doctors[0]["verified_by"])
    ids = [d["id"] for d in doctors[:2]]
    created = client.post(f"/api/cases/{cid}/opinions", headers=auth(tok_a),
                          json={"doctor_ids": ids}).json()
    check("drafted requests linked to package version",
          created["requests"][0]["case_package_version_id"] is not None)
    oid1, oid2 = created["requests"][0]["id"], created["requests"][1]["id"]
    client.patch(f"/api/opinions/{oid1}", headers=auth(tok_a),
                 json={"action": "mark_sent"})
    client.patch(f"/api/opinions/{oid2}", headers=auth(tok_a), json={"action": "mark_sent"})
    # force SLA breach directly in DB
    from datetime import datetime, timedelta
    from app.database import SessionLocal
    from app.models import OpinionRequest
    db = SessionLocal()
    db.query(OpinionRequest).filter(OpinionRequest.id == oid1).update(
        {"sla_deadline": datetime.utcnow() - timedelta(days=1)})
    db.commit(); db.close()
    sla = client.post(f"/api/cases/{cid}/opinions/sla-check", headers=auth(tok_a)).json()
    check("SLA breach flagged no_response", sla["flagged_no_response"] >= 1)
    client.patch(f"/api/opinions/{oid1}", headers=auth(tok_a),
                 json={"action": "respond", "response": {"opinion_recommended_modality": "Surgery first"}})
    client.patch(f"/api/opinions/{oid2}", headers=auth(tok_a),
                 json={"action": "respond", "response": {"opinion_recommended_modality": "Chemoradiation first"}})
    comp = client.get(f"/api/cases/{cid}/opinions/comparison", headers=auth(tok_a)).json()
    check("conflict detected across modalities", comp["conflict_detected"] is True)
    check("comparison has both columns", len(comp["columns"]) == 2)

    print("== feature 6: logistics ==")
    centers = client.get("/api/centers?capability=proton").json()
    check("center finder filters by capability",
          any("Proton" in c["name"] for c in centers))
    client.post("/api/wait-reports", headers=auth(tok_a),
                json={"center_name": "Tata Memorial Centre (TMH)", "reported_wait_days": 21})
    client.post("/api/wait-reports", headers=auth(tok_a),
                json={"center_name": "Tata Memorial Centre (TMH)", "reported_wait_days": 35})
    summary = client.get("/api/centers/wait-summary").json()
    tata = next(s for s in summary if "Tata" in s["center_name"])
    check("wait-time aggregation averages reports", abs(tata["avg_recent_wait_days"] - 28.0) < 0.1)
    tr = client.post(f"/api/cases/{cid}/transfers", headers=auth(tok_a),
                     json={"from_hospital": "Local hospital", "to_hospital": "Tata Memorial Centre (TMH)"}).json()
    client.patch(f"/api/transfers/{tr['id']}?status=received", headers=auth(tok_a))
    transfers = client.get(f"/api/cases/{cid}/transfers", headers=auth(tok_a)).json()
    check("transfer status advanced", transfers[0]["status"] == "received")

    print("== feature 7: trials ==")
    trials = client.get("/api/trials/search", params={"cancer_type": "breast"},
                        headers=auth(tok_a)).json()
    check("trial search returns envelope", isinstance(trials.get("results"), list))
    check("every trial has live/placeholder flags",
          all(("live" in t and "placeholder" in t) for t in trials["results"]))
    check("source note present", bool(trials.get("source_note")))
    check("offline fallback yields examples when live disabled",
          all(t["external_id"].startswith("CTRI-EXAMPLE") or t["external_id"].startswith("NCT-EXAMPLE")
              for t in client.get("/api/trials/search", params={"cancer_type": "breast", "live": "false"},
                                  headers=auth(tok_a)).json()["results"]))

    print("== feature 8: finance ==")
    client.put(f"/api/cases/{cid}/financial-profile", headers=auth(tok_a),
               json={"insurance_status": "uninsured", "income_bracket": "low"})
    match = client.post(f"/api/cases/{cid}/coverage-match", headers=auth(tok_a)).json()
    pmjay = next(r for r in match["results"] if "PM-JAY" in r["scheme_name"])
    check("PM-JAY matched for low-income uninsured", pmjay["status"] in ("eligible", "needs_verification"))
    gap_flags = [f for f in client.get(f"/api/cases/{cid}/flags", headers=auth(tok_a)).json()
                 if f["flag_type"] == "coverage_gap"]
    check("network-mismatch coverage-gap flag created", len(gap_flags) >= 1)
    pub = client.post("/api/coverage-check", json={
        "insurance_status": "uninsured", "income_bracket": "low",
        "employment": "central_government_pensioner"}).json()
    cghs = next(r for r in pub["results"] if "CGHS" in r["scheme_name"])
    check("public quick-check matches CGHS for pensioner", cghs["status"] == "eligible")
    check("quick-check carries disclaimer", "not medical advice" in pub["disclaimer"])

    print("== new: manual records, share links, demo account ==")
    rec = client.post(f"/api/cases/{cid}/records", headers=auth(tok_a), json={
        "extracted_date": "2026-08-01", "extracted_source": "City Lab",
        "extracted_doc_type": "Lab report", "key_findings": ["Haemoglobin 9.2 g/dL"]}).json()
    check("manual record added without file",
          rec["has_file"] is False and rec["extracted_doc_type"] == "Lab report")
    r = client.get(f"/api/documents/{rec['id']}/file", headers=auth(tok_a))
    check("file download correctly refused for manual record", r.status_code == 404)
    share = client.post(f"/api/packages/{p1['id']}/share-link", headers=auth(tok_a)).json()
    check("share link created", share["share_path"].startswith("/package/"))
    pub_pkg = client.get(f"/api/public/packages/{p1['id']}/{share['share_path'].split('/')[-1]}")
    check("public share view works WITHOUT auth token",
          pub_pkg.status_code == 200 and pub_pkg.json()["snapshot_json"]["case"]["patient_name"] == "Test Patient")
    bad = client.get(f"/api/public/packages/{p1['id']}/wrong-token")
    check("wrong share token rejected", bad.status_code == 404)
    demo_login = client.post("/api/auth/login", json={"email": "demo@navigator.app", "password": "demo1234"})
    check("demo account seeded & login works", demo_login.status_code == 200)
    demo_tok = demo_login.json()["token"]
    demo_cases = client.get("/api/cases", headers=auth(demo_tok)).json()
    check("demo case present with documents", len(demo_cases) >= 1)

    print("== new: hospital comparison + DPDP rights ==")
    centers = client.get("/api/centers").json()
    top = centers[0]
    check("centres ranked by objective score with breakdown",
          top["objective_score"]["total"] > 0 and
          set(top["objective_score"]["breakdown"]) >= {"public_or_nonprofit_ownership",
                                                       "national_accreditation_noted"})
    check("centre notes carry verifiable sources",
          all(n.get("source_url") for c in centers for n in c["notes"]))
    corp = next(c for c in centers if "Apollo" in c["name"])
    check("corporate ownership recorded as neutral fact (no bonus)",
          corp["objective_score"]["breakdown"]["public_or_nonprofit_ownership"] == 0)

    print("== global expansion ==")
    us = [c for c in centers if c.get("country") == "US"]
    check("global centres seeded (US present with NCI designation)",
          len(us) >= 3 and any(
              n["note_type"] == "designation" and "NCI-Designated Comprehensive" in n["detail"]
              for c in us for n in c["notes"]))
    mda = next(c for c in centers if "MD Anderson" in c["name"])
    check("designation factor scores (MD Anderson gets +4 tier)",
          mda["objective_score"]["breakdown"]["institutional_designation"] == 4)
    gb = client.get("/api/centers", params={"country": "GB"}).json()
    check("country filter works", 0 < len(gb) <= 3 and all(c["country"] == "GB" for c in gb))
    method = client.get("/api/centers/methodology").json()
    check("methodology includes designation tiers + self-check links",
          "institutional_designation" in method["weights"] and
          bool(method.get("designation_tiers")) and
          len(method["verify_any_hospital_yourself"]) >= 4)
    schemes_us = client.get("/api/schemes", params={"country": "US"}).json()
    check("schemes scoped by country", len(schemes_us) >= 3 and
          all(s["scheme_name"].endswith("(US)") or "501(r)" in s["scheme_name"] or "Medicaid" in s["scheme_name"]
              or "Medicare" in s["scheme_name"] or "ACA" in s["scheme_name"] for s in schemes_us))

    print("== personalization: My Plan ==")
    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth(tok_a)).json()
    check("plan returns country, centres, schemes, trials, questions",
          plan["country"] == "IN" and isinstance(plan["local_centres"], list)
          and isinstance(plan["schemes"], list) and isinstance(plan["trials"], list))
    check("plan questions generated from open flags",
          len(plan["questions_to_ask"]) >= 1 and plan["questions_to_ask"][0]["question"])
    case_gb = client.post("/api/cases", headers=auth(tok_a), json={
        "patient_name": "GB Patient", "cancer_type": "breast", "country": "GB"}).json()
    client.put(f"/api/cases/{case_gb['id']}/financial-profile", headers=auth(tok_a),
               json={"insurance_status": "uninsured", "income_bracket": "low"})
    plan_gb = client.get(f"/api/cases/{case_gb['id']}/personal-plan", headers=auth(tok_a)).json()
    check("plan respects case country (GB gets NHS)",
          plan_gb["country"] == "GB" and
          any("NHS" in s["scheme_name"] for s in plan_gb["schemes"]) and
          all(s["status"] == "eligible" for s in plan_gb["schemes"]))
    exp = client.get("/api/me/export", headers=auth(tok_a)).json()
    check("DPDP right of access: full export works", len(exp["cases"]) >= 1)
    deleted = client.delete("/api/me", headers=auth(tok_b)).json()
    check("DPDP right to erasure: account deleted", deleted["deleted"] is True)
    check("deleted family cannot login",
          client.post("/api/auth/login", json={"email": "fam-b@test.com",
                                               "password": "secret2"}).status_code == 401)

print(f"\nALL {PASS} SMOKE CHECKS PASSED")
