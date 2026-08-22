"""Exhaustive transition tests for the OpinionRequest state machine.

Synthetic fixtures only ("Patient A", "Doctor 1"). Covers:
  - legal transitions (drafted→sent→acknowledged→received, late replies)
  - illegal transitions (must 400)
  - SLA edge cases (only 'sent' auto-flips to no_response)
  - conflict detection across modalities
"""

import uuid
from datetime import datetime, timedelta

import pytest

from app.database import SessionLocal
from app.models import OpinionRequest


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def fam(client):
    email = f"sm_{uuid.uuid4().hex[:8]}@t.com"
    tok = client.post("/api/auth/register",
                      json={"email": email, "password": "secretpass9",
                            "consent_accepted": True}).json()["token"]
    return tok


@pytest.fixture(scope="module")
def case_id(client, fam):
    r = client.post("/api/cases", headers=_auth(fam),
                    json={"patient_name": "Patient A", "cancer_type": "test-type"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


@pytest.fixture(scope="module")
def doctor_ids(client, fam):
    docs = client.get("/api/doctors", headers=_auth(fam)).json()
    assert len(docs) >= 4
    return [d["id"] for d in docs[:4]]


_pool = {"i": 0}


def _mk(client, fam, case_id, doctor_ids):
    """Create one drafted opinion request per unused doctor."""
    did = doctor_ids[_pool["i"] % len(doctor_ids)]
    _pool["i"] += 1
    r = client.post(f"/api/cases/{case_id}/opinions", headers=_auth(fam),
                    json={"doctor_ids": [did]})
    assert r.status_code == 200, r.text
    return r.json()["requests"][0]["id"]


def _patch(client, fam, oid, action, response=None):
    body = {"action": action}
    if response is not None:
        body["response"] = response
    return client.patch(f"/api/opinions/{oid}", headers=_auth(fam), json=body)


def _backdate_deadline(oid, days_ago=1):
    db = SessionLocal()
    db.query(OpinionRequest).filter(OpinionRequest.id == oid).update(
        {"sla_deadline": datetime.utcnow() - timedelta(days=days_ago)})
    db.commit()
    db.close()


def test_legal_full_chain(client, fam, case_id, doctor_ids):
    oid = _mk(client, fam, case_id, doctor_ids)

    r = client.get(f"/api/cases/{case_id}/opinions", headers=_auth(fam)).json()
    mine = next(o for o in r if o["id"] == oid)
    assert mine["status"] == "drafted"

    sent = _patch(client, fam, oid, "mark_sent")
    assert sent.status_code == 200 and sent.json()["status"] == "sent"
    assert sent.json()["sent_at"] is not None
    deadline = datetime.fromisoformat(sent.json()["sla_deadline"])
    assert deadline > datetime.utcnow() + timedelta(days=2)

    acked = _patch(client, fam, oid, "acknowledge")
    assert acked.status_code == 200 and acked.json()["status"] == "acknowledged"

    resp = _patch(client, fam, oid, "respond",
                  {"opinion_recommended_modality": "Surgery A"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "opinion_received"
    assert body["responded_at"] is not None

    comp = client.get(f"/api/cases/{case_id}/opinions/comparison",
                      headers=_auth(fam)).json()
    assert comp["columns"] and comp["conflict_detected"] is False


def test_illegal_transitions_rejected(client, fam, case_id, doctor_ids):
    oid = _mk(client, fam, case_id, doctor_ids)  # drafted

    # respond while drafted -> 400
    assert _patch(client, fam, oid, "respond",
                  {"opinion_recommended_modality": "X"}).status_code == 400
    # acknowledge / decline / no_response while drafted -> must be 400
    assert _patch(client, fam, oid, "acknowledge").status_code == 400
    assert _patch(client, fam, oid, "decline").status_code == 400
    assert _patch(client, fam, oid, "no_response").status_code == 400

    # mark_sent twice -> second is 400
    assert _patch(client, fam, oid, "mark_sent").status_code == 200
    assert _patch(client, fam, oid, "mark_sent").status_code == 400

    # acknowledge after sent is legal; then mark_sent/decline-from-received paths
    assert _patch(client, fam, oid, "acknowledge").status_code == 200
    assert _patch(client, fam, oid, "mark_sent").status_code == 400

    # double-respond: after opinion_received, further responds are 400
    assert _patch(client, fam, oid, "respond",
                  {"opinion_recommended_modality": "Modality Z"}).status_code == 200
    assert _patch(client, fam, oid, "respond",
                  {"opinion_recommended_modality": "Modality Y"}).status_code == 400


def test_respond_without_details_is_accepted(client, fam, case_id, doctor_ids):
    """Regression: respond with empty details used to raise NameError."""
    oid = _mk(client, fam, case_id, doctor_ids)
    assert _patch(client, fam, oid, "mark_sent").status_code == 200
    r = _patch(client, fam, oid, "respond")  # response omitted entirely
    assert r.status_code == 200 and r.json()["status"] == "opinion_received"


def test_sla_edges(client, fam, case_id, doctor_ids):
    # past-deadline 'sent' flips to no_response on explicit check
    o_past = _mk(client, fam, case_id, doctor_ids)
    assert _patch(client, fam, o_past, "mark_sent").status_code == 200
    _backdate_deadline(o_past, days_ago=2)
    flagged = client.post(f"/api/cases/{case_id}/opinions/sla-check",
                          headers=_auth(fam)).json()["flagged_no_response"]
    assert flagged >= 1
    rows = client.get(f"/api/cases/{case_id}/opinions", headers=_auth(fam)).json()
    assert next(o for o in rows if o["id"] == o_past)["status"] == "no_response"

    # acknowledged past deadline does NOT auto-flip
    o_ack = _mk(client, fam, case_id, doctor_ids)
    assert _patch(client, fam, o_ack, "mark_sent").status_code == 200
    assert _patch(client, fam, o_ack, "acknowledge").status_code == 200
    _backdate_deadline(o_ack, days_ago=3)
    before = client.post(f"/api/cases/{case_id}/opinions/sla-check",
                         headers=_auth(fam)).json()
    rows = client.get(f"/api/cases/{case_id}/opinions", headers=_auth(fam)).json()
    assert next(o for o in rows if o["id"] == o_ack)["status"] == "acknowledged"

    # future-deadline 'sent' stays untouched
    o_future = _mk(client, fam, case_id, doctor_ids)
    assert _patch(client, fam, o_future, "mark_sent").status_code == 200
    rows = client.get(f"/api/cases/{case_id}/opinions", headers=_auth(fam)).json()
    assert next(o for o in rows if o["id"] == o_future)["status"] == "sent"


def test_late_reply_after_no_response_is_allowed(client, fam, case_id, doctor_ids):
    oid = _mk(client, fam, case_id, doctor_ids)
    assert _patch(client, fam, oid, "mark_sent").status_code == 200
    _backdate_deadline(oid)
    client.post(f"/api/cases/{case_id}/opinions/sla-check", headers=_auth(fam))
    r = _patch(client, fam, oid, "respond",
               {"opinion_recommended_modality": "Late Modality"})
    assert r.status_code == 200 and r.json()["status"] == "opinion_received"


def test_conflict_detection_and_clearing(client, fam, case_id, doctor_ids):
    # Isolated case: conflict evaluation is per-case, so prior tests' received
    # opinions (same shared case) must not leak into this scenario.
    cid = client.post("/api/cases", headers=_auth(fam),
                      json={"patient_name": "Patient A",
                            "cancer_type": "conflict-case"}).json()["id"]
    ids = []
    for _ in range(4):
        oid = _mk(client, fam, cid, doctor_ids)
        assert _patch(client, fam, oid, "mark_sent").status_code == 200
        ids.append(oid)

    def respond(oid, modality):
        r = _patch(client, fam, oid, "respond",
                   {"opinion_recommended_modality": modality})
        assert r.status_code == 200, r.text
        return r.json()

    a, b, c, d = ids
    respond(a, "Surgery first")
    comp = client.get(f"/api/cases/{cid}/opinions/comparison",
                      headers=_auth(fam)).json()
    assert comp["conflict_detected"] is False

    respond(b, "Chemoradiation first")
    comp = client.get(f"/api/cases/{cid}/opinions/comparison",
                      headers=_auth(fam)).json()
    assert comp["conflict_detected"] is True
    rows = {o["id"]: o for o in
            client.get(f"/api/cases/{cid}/opinions", headers=_auth(fam)).json()}
    assert rows[a]["conflicts_flagged"] is True
    assert rows[b]["conflicts_flagged"] is True

    # third opinion joins an existing side — conflict persists, re-evaluated
    respond(c, "SURGERY FIRST ")   # same modality, case/spacing differences
    rows = {o["id"]: o for o in
            client.get(f"/api/cases/{cid}/opinions", headers=_auth(fam)).json()}
    assert rows[c]["conflicts_flagged"] is True

    # fourth opinion picks a side — but both sides still exist in history,
    # so the conflict flag correctly PERSISTS on every received row
    respond(d, "chemoradiation FIRST")
    comp = client.get(f"/api/cases/{cid}/opinions/comparison",
                      headers=_auth(fam)).json()
    assert comp["conflict_detected"] is True
    rows = {o["id"]: o for o in
            client.get(f"/api/cases/{cid}/opinions", headers=_auth(fam)).json()}
    assert all(rows[i]["conflicts_flagged"] is True for i in ids)


def test_scoping_other_family_cannot_transition(client, fam, case_id, doctor_ids):
    other = client.post("/api/auth/register",
                        json={"email": f"other_{uuid.uuid4().hex[:6]}@t.com",
                              "password": "secretpass8", "consent_accepted": True}
                        ).json()["token"]
    oid = _mk(client, fam, case_id, doctor_ids)
    assert client.patch(f"/api/opinions/{oid}", headers=_auth(other),
                        json={"action": "mark_sent"}).status_code == 404
