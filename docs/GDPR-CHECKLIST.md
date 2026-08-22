# GDPR Compliance Checklist (Art.-by-Art.)

Status legend: ✅ implemented · 🟡 template/process needed · ⛔ not applicable

| Article | Requirement | Status | Where / Evidence |
|---|---|---|---|
| Art. 5 | Principles: lawfulness, minimisation, purpose limitation, storage limitation | ✅ | Itemised notice (`/api/legal/ropa`, Privacy page); optional finance fields; retention = until deletion |
| Art. 6 + 9 | Lawful basis; explicit consent for health data | ✅ | Consent gate at registration (server-enforced), withdrawal as easy as giving (delete account) |
| Art. 12–14 | Transparent information | ✅ | Plain-language Privacy page + per-form "why we ask" hints |
| Art. 15 | Right of access | ✅ | `GET /api/me/export` (machine-readable JSON) + Dashboard button |
| Art. 16 | Rectification | ✅ | Every field editable in-app; extraction correction UI |
| Art. 17 | Erasure | ✅ | `DELETE /api/me` cascades cases, documents (+files), flags, opinions, packages, transfers, profiles, wait reports; audited |
| Art. 18/20 | Restriction & portability | 🟡 | Portability = JSON export ✅; restriction requests → grievance channel (manual) |
| Art. 21–22 | Objection; automated decisions | ✅ | No solely-automated decisions about treatment; ranking/plan are informational with published methodology |
| Art. 25 | Data protection by design | 🟡 | Family-scoped queries, minimal fields, share links revocable & token-gated; pseudonymisation is roadmap |
| Art. 30 | Records of processing (ROPA) | ✅ | `GET /api/legal/ropa` |
| Art. 32 | Security of processing | ✅ | PBKDF2(200k)+JWT, ownership checks on every route, rate limiting, upload caps, CORS allow-list, TLS via Caddy in compose, audit trail table |
| Art. 33–34 | Breach notification (72 h) | 🟡 | Documented process in Privacy/Terms; incident-response runbook = TODO before launch |
| Art. 35 | DPIA | 🟡 | Health data at scale likely triggers DPIA — complete before real patients (template below) |
| Ch. V | International transfers | ✅ documented | Deployment guidance: host EEA users in EEA region (Render EU / Neon EU region) or rely on provider SCCs |
| Art. 37–39 | DPO | 🟡 | Grievance-officer placeholder exists; appoint DPO only if designated SDF/large-scale |

## Pre-launch TODO (process items)
1. Lawyer review of Privacy/Terms/DPIA for each target market.
2. Fill Grievance Officer + DPO details; publish response times.
3. Write breach-response runbook (who, how, templates).
4. Enable server-side audit-log review cadence (table `audit_log`).
5. If using Render/Neon free tiers for EU users: switch to their EU regions.

## DPIA quick-start questions
- What health data? (case fields you type, uploaded records, financial profile)
- Who can see it? (only your family account; token-gated shares YOU send)
- Retention? (until self-service deletion)
- Transfers? (depends on chosen hosting region)
- Risks & mitigations? (unauthorised access → auth+scoping+TLS; over-retention → erasure endpoint; function creep → no ads/no sale promise in Terms)
