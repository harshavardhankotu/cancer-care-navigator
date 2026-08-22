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
                      json={"email": "no-consent@test.com", "password": "secretpass1"}).status_code == 400)
    check("weak password rejected (too short)",
          client.post("/api/auth/register",
                      json={"email": "weak1@test.com", "password": "short1", "consent_accepted": True}).status_code == 400)
    check("common password rejected",
          client.post("/api/auth/register",
                      json={"email": "weak2@test.com", "password": "1234567890", "consent_accepted": True}).status_code == 400)
    tok_a = client.post("/api/auth/register", json={"email": "fam-a@test.com", "password": "secretpass1",
                                                    "consent_accepted": True}).json()["token"]
    tok_b = client.post("/api/auth/register", json={"email": "fam-b@test.com", "password": "secretpass2",
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

    # Digital PDFs must be READ (pdf_text mode), proving the free extraction pipeline.
    from reportlab.pdfgen import canvas as _rl_canvas
    from io import BytesIO as _B
    buf = _B()
    c = _rl_canvas.Canvas(buf)
    c.drawString(72, 780, "PATHOLOGY REPORT")
    c.drawString(72, 762, "City Care Hospital, Oncology Lab")
    c.drawString(72, 744, "Date: 2026-03-15")
    c.drawString(72, 726, "Finding: adenocarcinoma; biomarker panel pending")
    c.save()
    digital = buf.getvalue()
    r2 = client.post(f"/api/cases/{cid}/documents", headers=auth(tok_a),
                     files={"file": ("biopsy-pathology.pdf", _B(digital), "application/pdf")})
    d2 = r2.json()
    check("digital PDF auto-read via pypdf (pdf_text mode)",
          d2["raw_extraction_json"]["extraction_mode"] == "pdf_text"
          and "Pathology" in (d2["extracted_doc_type"] or ""))
    check("date extracted from PDF text", d2["extracted_date"] is not None)

    # Oversized uploads must be rejected without reading everything into memory.
    from app.services import storage as storage_mod
    old_cap = storage_mod.MAX_UPLOAD_BYTES
    try:
        storage_mod.MAX_UPLOAD_BYTES = 64
        big = client.post(f"/api/cases/{cid}/documents", headers=auth(tok_a),
                          files={"file": ("big.pdf", _B(b"x" * 100), "application/pdf")})
        check("oversized upload rejected (413)", big.status_code == 413)
    finally:
        storage_mod.MAX_UPLOAD_BYTES = old_cap

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
    client.post(f"/api/packages/{p1['id']}/share-revoke", headers=auth(tok_a))
    revoked = client.get(f"/api/public/packages/{p1['id']}/{share['share_path'].split('/')[-1]}")
    check("revoked share link stops working", revoked.status_code == 404)
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
    check("schemes scoped by country (incl. hidden NORD entry)", len(schemes_us) >= 4
          and all(s["country"] == "US" for s in schemes_us))

    print("== personalization: My Plan ==")
    plan = client.get(f"/api/cases/{cid}/personal-plan", headers=auth(tok_a)).json()
    check("plan returns country, centres, schemes, trials, questions",
          plan["country"] == "IN" and isinstance(plan["local_centres"], list)
          and isinstance(plan["schemes"], list) and isinstance(plan["trials"], list))
    check("plan questions generated from open flags",
          len(plan["questions_to_ask"]) >= 1 and plan["questions_to_ask"][0]["question"])
    check("audience framing present (broke vs budgeted)", bool(plan["audience_note"]))
    hidden = [s for s in plan["schemes"] if s.get("category") == "travel"]
    check("hidden subsidies (rail concession) surface first for IN", len(hidden) >= 1)

    print("== trials depth + freemium tier ==")
    live = client.get("/api/trials/search", params={"cancer_type": "breast", "country": "IN"},
                      headers=auth(tok_a)).json()["results"]
    enriched = next((t for t in live if t.get("live")), None)
    if enriched:
        check("trials carry phase/enrolment/interventions/priority",
              all(k in enriched for k in ("phase_label", "enrollment", "interventions",
                                          "priority_score", "priority_why")))
        scores = [t["priority_score"] for t in live if t.get("live")]
        check("trials ordered by importance after country priority", scores == sorted(scores, reverse=True))
    else:
        print("  skip - offline: no live trial data available")
    free_plan = client.get(f"/api/cases/{cid}/personal-plan?extended=true",
                           headers=auth(tok_a)).json()
    check("free tier stays capped at 6 centres", len(free_plan["global_centres"]) <= 6)
    from app.database import SessionLocal as _SL
    from app.models import Family as _Fam
    _db = _SL()
    _db.query(_Fam).filter(_Fam.email == "fam-a@test.com").update({"plan_tier": "supporter"})
    _db.commit(); _db.close()
    case_s = client.post("/api/cases", headers=auth(tok_a),
                         json={"patient_name": "Supporter Case", "cancer_type": "breast"}).json()
    sup_plan = client.get(f"/api/cases/{case_s['id']}/personal-plan?extended=true",
                          headers=auth(tok_a)).json()
    check("supporter tier unlocks extended lists",
          sup_plan["plan_tier"] == "supporter"
          and len(sup_plan["global_centres"]) >= len(free_plan["global_centres"]))

    print("== legal: region-aware privacy notes ==")
    de = client.get("/api/legal/region-notes", params={"country": "DE"}).json()
    check("EU note served for Germany", "GDPR" in de["law"])
    usn = client.get("/api/legal/region-notes", params={"country": "US"}).json()
    check("US note covers state laws (WA My Health My Data)", "My Health My Data" in str(usn))
    allr = client.get("/api/legal/region-notes").json()
    check("region notes cover 15+ jurisdictions", len(allr) >= 15)

    print("== security: brute-force lockout ==")
    codes = []
    for _ in range(11):
        rr = client.post("/api/auth/login",
                         json={"email": "fam-a@test.com", "password": "wrongpass99"})
        codes.append(rr.status_code)
    check("brute force rate-limited (429 after burst)", 429 in codes)
    # wait — fam-a is still valid; ensure legit login still works from same IP+email? It is
    # rate-limited by design for this window; use a different account to confirm service.
    ok = client.post("/api/auth/login", json={"email": "demo@navigator.app", "password": "demo1234"})
    check("other accounts unaffected by lockout", ok.status_code == 200)
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
                                               "password": "secretpass2"}).status_code == 401)

    print("== erasure completeness (wait reports) ==")
    client.delete("/api/me", headers=auth(tok_a))
    summary_after = client.get("/api/centers/wait-summary").json()
    tata_left = [s for s in summary_after if "Tata" in s["center_name"]]
    check("user's crowdsourced reports erased with account", len(tata_left) == 0)

    print("== intercountry + contacts + GDPR artifacts ==")
    de = client.get("/api/legal/international-access", params={"country": "DE"}).json()
    check("EU cross-border directive served for DE",
          any("2011/24/EU" in n["title"] for n in de["for_your_country"]))
    inn = client.get("/api/legal/international-access", params={"country": "IN"}).json()
    check("India e-Medical visa note served", any("e-Medical" in n["title"] for n in inn["for_your_country"]))
    check("general cross-border guidance present", len(de["general"]) >= 2)
    centers_all = client.get("/api/centers").json()
    with_site = [c for c in centers_all if c.get("website")]
    check("official website contact published for 30+ centres", len(with_site) >= 30)
    from app.database import SessionLocal as _SL2
    from app.models import AuditLog as _AL
    _db2 = _SL2()
    actions = {a[0] for a in _db2.query(_AL.action).all()}
    _db2.close()
    needed = {"register", "login_fail", "export", "erase", "share_create", "share_revoke"}
    check("audit trail records security events (GDPR Art.30/32)", needed.issubset(actions))

print(f"\nALL {PASS} SMOKE CHECKS PASSED")
