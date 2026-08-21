"""Clinical trial search with depth: which trials matter, and why.

ZERO-COST live integration: ClinicalTrials.gov Data API v2 is public domain and
requires NO API key. CTRI publishes no public API, so CTRI coverage remains a
seeded placeholder pending an official interface.

For every live study we extract: phase, enrolment size, sponsor, interventions,
eligibility basics and a short summary — then compute a transparent PRIORITY
score so families can see which studies are likely most consequential:

    priority = phase weight + enrolment weight + in-country sites bonus

The ordering is a heuristic to aid reading, NOT medical advice; eligibility is
always decided by the trial team. Keep signatures stable — this is the swap
point for future registry integrations.
"""

import json
import urllib.parse
import urllib.request

from sqlalchemy.orm import Session

from ..models import Trial

API_BASE = "https://clinicaltrials.gov/api/v2/studies"

PHASE_WEIGHTS = [
    ("PH3", 40), ("PH2/PH3", 36), ("PHASE3", 40), ("Phase 3", 40),
    ("PHASE2", 26), ("Phase 2", 26), ("PHASE1/PHASE2", 14), ("PHASE1", 10),
]


def _phase_label(phases: list) -> str:
    p = [x.upper() for x in phases or []]
    if "PHASE3" in p:
        return "Phase 3"
    if "PHASE2" in p and "PHASE3" in p:
        return "Phase 2/3"
    if "PHASE2" in p:
        return "Phase 2"
    if "PHASE1" in p and "PHASE2" in p:
        return "Phase 1/2"
    if "EARLY_PHASE1" in p:
        return "Early Phase 1"
    if "PHASE1" in p:
        return "Phase 1"
    return "Not applicable (observational/other)"


def _phase_weight(label: str) -> int:
    for key, w in PHASE_WEIGHTS:
        if key in label.upper():
            return w
    return 4


def _priority(phase_weight: int, enrollment, country_sites: int) -> dict:
    enr = enrollment if isinstance(enrollment, (int, float)) else 0
    enr_w = min(20, int(enr / 50))
    local_bonus = min(15, country_sites * 5)
    score = phase_weight + enr_w + local_bonus
    why = []
    if phase_weight >= 40:
        why.append("Phase 3 — results at this stage often change standard of care")
    elif phase_weight >= 26:
        why.append("Phase 2 — tests whether a treatment works; still research")
    if enr >= 300:
        why.append(f"Large study (~{int(enr):,} participants)")
    if local_bonus:
        why.append("Has recruiting sites near you")
    return {"score": score, "why": why}


def _parse_locations(module) -> list[dict]:
    out = []
    for l in module or []:
        out.append({
            "facility": str(l.get("facility") or "?"),
            "city": str(l.get("city") or ""),
            "country": str(l.get("country") or "").lower(),
        })
    return out


def _live_ctg_search(cancer_type: str | None, biomarkers: list[str] | None,
                     country: str | None) -> list[dict]:
    params = {
        "query.cond": cancer_type or "cancer",
        "filter.overallStatus": "RECRUITING",
        "pageSize": "25",
    }
    if biomarkers:
        params["query.term"] = " OR ".join(biomarkers)
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "cancer-care-navigator-mvp/0.1"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())

    ctry = (country or "").lower()
    out = []
    for study in data.get("studies", [])[:25]:
        p = study.get("protocolSection", {})
        ident = p.get("identificationModule", {})
        status = p.get("statusModule", {})
        design = p.get("designModule", {}) or {}
        arms = (p.get("armsInterventionsModule", {}) or {}).get("interventions") or []
        sponsor = ((p.get("sponsorCollaboratorsModule", {}) or {}).get("leadSponsor") or {}).get("name")
        elig = p.get("eligibilityModule", {}) or {}

        locations = _parse_locations((p.get("contactsLocationsModule") or {}).get("locations"))
        local = [l for l in locations if ctry and l["country"] == ctry]

        nct = ident.get("nctId", "")
        label = _phase_label(design.get("phases"))
        enrollment = ((design.get("enrollmentInfo") or {}).get("count")) or 0
        prio = _priority(_phase_weight(label), enrollment, len(local))

        summary = ((p.get("descriptionModule", {}) or {}).get("briefSummary") or "").strip()

        out.append({
            "source": "ClinicalTrials.gov",
            "external_id": nct,
            "title": ident.get("briefTitle") or "(no title)",
            "cancer_types": (p.get("conditionsModule", {}) or {}).get("conditions") or [],
            "biomarkers": [],
            "location": "; ".join(
                f"{l['facility']} — {l['city']}, {l['country'].title()}".strip(", ")
                for l in (local[:3] or locations[:3])
            ) or "See registry listing",
            "status": status.get("overallStatus") or "Unknown",
            "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
            "country_sites": len(local),
            "phase_label": label,
            "enrollment": int(enrollment or 0),
            "sponsor": sponsor,
            "interventions": [i.get("name") for i in arms if i.get("name")][:3],
            "summary_snippet": (summary[:220] + "…") if len(summary) > 220 else summary,
            "sex_eligible": elig.get("sex"),
            "min_age": elig.get("minimumAge"),
            "priority_score": prio["score"],
            "priority_why": prio["why"],
            "live": True,
            "placeholder": False,
        })

    # Personalisation first, then importance.
    out.sort(key=lambda s: (-s["country_sites"], -s["priority_score"]))
    return out


def _seeded_examples(db: Session, cancer_type: str | None,
                     biomarkers: list[str] | None) -> list[dict]:
    ct = (cancer_type or "").lower().strip()
    bms = [b.lower().strip() for b in (biomarkers or []) if b and b.strip()]
    out = []
    for trial in db.query(Trial).all():
        types = [t.lower() for t in (trial.cancer_types or [])]
        tbms = [b.lower() for b in (trial.biomarkers or [])]
        type_ok = (not ct) or any(ct in t or t in ct for t in types)
        bm_ok = (not bms) or bool(set(bms) & set(tbms))
        if type_ok and bm_ok:
            out.append({
                "source": trial.source,
                "external_id": trial.external_id,
                "title": trial.title,
                "cancer_types": trial.cancer_types or [],
                "biomarkers": trial.biomarkers or [],
                "location": trial.location,
                "status": trial.status,
                "url": trial.url,
                "country_sites": 0,
                "phase_label": "Example entry",
                "enrollment": 0,
                "sponsor": None,
                "interventions": [],
                "summary_snippet": None,
                "sex_eligible": None,
                "min_age": None,
                "priority_score": 0,
                "priority_why": [],
                "live": False,
                "placeholder": True,
            })
    return out


def search_trials(db: Session, cancer_type: str | None, biomarkers: list[str] | None,
                  include_live: bool = True, country: str | None = None) -> dict:
    results = []
    source_note = "seeded examples only"
    if include_live:
        try:
            results = _live_ctg_search(cancer_type, biomarkers, country)
            if results:
                source_note = ("LIVE ClinicalTrials.gov (recruiting worldwide). Ordered by: "
                               "sites in your country → importance (phase, size).")
        except Exception:
            results = []
    if not results:
        results = _seeded_examples(db, cancer_type, biomarkers)
        source_note = ("Offline fallback: seeded example records "
                       "(CTRI has no public API; live search covers ClinicalTrials.gov)")
    return {"results": results[:10], "source_note": source_note}
