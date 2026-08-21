"""Clinical trial search.

ZERO-COST live integration: ClinicalTrials.gov Data API v2 is public domain and
requires NO API key. CTRI (ctri.nic.in) publishes no public API, so CTRI
coverage remains a seeded-example placeholder pending an official interface.

Behaviour:
  1. Try the live ClinicalTrials.gov v2 endpoint (stdlib urllib — no extra deps).
  2. If the network call fails (offline dev / blocked egress), fall back to the
     locally seeded example records so the feature still works for demos.

Every result carries `live: true|false` so the UI can badge it honestly.
Keep this signature stable — it is the swap point for a future CTRI integration.
"""

import json
import urllib.parse
import urllib.request

from sqlalchemy.orm import Session

from ..models import Trial

API_BASE = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = ("NCTId,BriefTitle,OverallStatus,Condition,BriefSummary,"
          "LocationCity,LocationCountry,LocationFacility")


def _live_ctg_search(cancer_type: str | None, biomarkers: list[str] | None) -> list[dict]:
    params = {
        "query.cond": cancer_type or "cancer",
        "filter.overallStatus": "RECRUITING",
        "pageSize": "10",
        "fields": FIELDS,
    }
    if biomarkers:
        params["query.term"] = " OR ".join(biomarkers)
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "cancer-care-navigator-mvp/0.1"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    out = []
    for study in data.get("studies", [])[:10]:
        p = study.get("protocolSection", {})
        ident = p.get("identificationModule", {})
        status = p.get("statusModule", {})
        locations = (p.get("contactsLocationsModule", {}) or {}).get("locations") or []
        india_locs = [l for l in locations if str(l.get("country", "")).lower() == "india"]
        shown = india_locs[:3] or locations[:3]
        loc_str = "; ".join(
            f"{l.get('facility', '?')} — {l.get('city', '')}, {l.get('country', '')}".strip(", ")
            for l in shown
        ) if shown else "See registry listing"
        nct = ident.get("nctId", "")
        out.append({
            "source": "ClinicalTrials.gov",
            "external_id": nct,
            "title": ident.get("briefTitle") or "(no title)",
            "cancer_types": (p.get("conditionsModule", {}) or {}).get("conditions") or [],
            "biomarkers": [],
            "location": loc_str,
            "status": status.get("overallStatus") or "Unknown",
            "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
            "india_sites": len(india_locs),
            "live": True,
            "placeholder": False,
        })
    return out


def _seeded_examples(db: Session, cancer_type: str | None, biomarkers: list[str] | None) -> list[dict]:
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
                "india_sites": 0,
                "live": False,
                "placeholder": True,
            })
    return out


def search_trials(db: Session, cancer_type: str | None, biomarkers: list[str] | None,
                  include_live: bool = True) -> dict:
    results = []
    source_note = "seeded examples only"
    if include_live:
        try:
            results = _live_ctg_search(cancer_type, biomarkers)
            if results:
                source_note = "LIVE ClinicalTrials.gov results (recruiting studies)"
        except Exception:
            results = []
    if not results:
        results = _seeded_examples(db, cancer_type, biomarkers)
        source_note = ("Offline fallback: seeded example records "
                       "(CTRI has no public API; live search covers ClinicalTrials.gov)")
    return {"results": results, "source_note": source_note}
