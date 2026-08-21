"""Region-specific privacy-law notes (public information, plain-language).

The Privacy page shows the note matching the user's country on top of the
global baseline. This is TEMPLATE content: accurate at the level of widely
published summaries, and explicitly flagged for lawyer review before launch.
"""

REGIME_BY_COUNTRY = {
    "IN": "IN", "US": "US", "GB": "GB", "CA": "CA", "AU": "AU",
    "DE": "EU", "FR": "EU", "NL": "EU", "IT": "EU", "ES": "EU", "PL": "EU",
    "BR": "BR", "JP": "JP", "KR": "KR", "SG": "SG", "AE": "AE", "EG": "GEN",
    "TR": "TR", "RU": "RU", "ZA": "ZA", "MX": "MX", "CN": "CN",
}

REGION_LEGAL_NOTES = {
    "IN": {
        "law": "Digital Personal Data Protection Act, 2023 (with DPDP Rules)",
        "regulator": "Data Protection Board of India",
        "points": [
            "Your consent must be free, specific, informed and given by a clear action — we record it at signup.",
            "You can access, correct, or erase your data; withdrawal of consent must be as easy as giving it.",
            "For patients under 18, verifiable consent of a parent or lawful guardian is required.",
            "Breaches affecting you must be reported to us → Board within 72 hours.",
        ],
    },
    "EU": {
        "law": "EU General Data Protection Regulation (GDPR)",
        "regulator": "your national Data Protection Authority",
        "points": [
            "Lawful basis for processing health data here is your explicit consent (Art. 9(2)(a)).",
            "Rights: access, rectification, erasure ('right to be forgotten'), restriction, portability, objection.",
            "Special-category health data requires explicit consent; you may withdraw at any time.",
            "Breaches are notified to the supervisory authority within 72 hours where required.",
        ],
    },
    "GB": {
        "law": "UK GDPR & Data Protection Act 2018",
        "regulator": "Information Commissioner's Office (ICO)",
        "points": [
            "Same core rights as GDPR: access, correction, erasure, portability.",
            "Explicit consent is our lawful basis for processing your health data.",
            "International transfers require adequacy or safeguards — see the security section below.",
        ],
    },
    "US": {
        "law": "No single federal health-privacy law covers consumer apps like this one (HIPAA applies to providers/insurers, not to us). State laws add rights:",
        "regulator": "state authorities (e.g., California Privacy Protection Agency)",
        "points": [
            "California (CCPA/CPRA): right to know, delete, correct, and opt out of 'sale/sharing' — we never sell data, so there is nothing to opt out of.",
            "Washington My Health My Data Act: separate consent for collecting consumer health data; sale of health data is prohibited — we don't sell.",
            "Ask the hospital about 501(r) charity-care policies regardless of this app.",
        ],
    },
    "CA": {
        "law": "PIPEDA (+ provincial health-privacy laws)",
        "regulator": "Office of the Privacy Commissioner of Canada",
        "points": [
            "Meaningful consent for collection/use/disclosure of personal information.",
            "You may access your records and challenge accuracy; withdrawal possible subject to legal limits.",
            "Provincial health laws (e.g., PHIPA in Ontario) can apply to health custodians; as a consumer tool we follow PIPEDA-grade practices.",
        ],
    },
    "AU": {
        "law": "Privacy Act 1988 (Australian Privacy Principles)",
        "regulator": "Office of the Australian Information Commissioner (OAIC)",
        "points": [
            "Collection must be necessary for our functions and handled per the APPs.",
            "You can request access and correction of your personal information.",
            "Sensitive information (health) needs your consent for collection.",
        ],
    },
    "BR": {
        "law": "Lei Geral de Proteção de Dados (LGPD)",
        "regulator": "Autoridade Nacional de Proteção de Dados (ANPD)",
        "points": [
            "Health data is 'sensitive personal data' — processed here only with your specific consent.",
            "Rights: confirmation, access, correction, anonymisation, deletion, portability.",
        ],
    },
    "JP": {
        "law": "Act on the Protection of Personal Information (APPI)",
        "regulator": "Personal Information Protection Commission (PPC)",
        "points": [
            "Purpose of use must be notified — see the itemised list above.",
            "You may request disclosure, correction, or cessation of use of your data.",
        ],
    },
    "KR": {
        "law": "Personal Information Protection Act (PIPA)",
        "regulator": "Personal Information Protection Commission (PIPC)",
        "points": [
            "Separate explicit consent is required for sensitive data including health.",
            "Access, correction, deletion, and suspension-of-processing rights apply.",
        ],
    },
    "SG": {
        "law": "Personal Data Protection Act (PDPA)",
        "regulator": "Personal Data Protection Commission Singapore",
        "points": [
            "Notification and consent obligations apply before collection.",
            "Access and correction rights available on request.",
        ],
    },
    "AE": {
        "law": "Federal Data Protection Law (Decree-Law No. 45 of 2021)",
        "regulator": "UAE Data Office",
        "points": [
            "Consent-based processing with rights of access, correction, and erasure.",
            "Health data handling follows additional sectoral requirements where applicable.",
        ],
    },
    "TR": {
        "law": "Kişisel Verilerin Korunması Kanunu (KVKK)",
        "regulator": "Kişisel Verileri Koruma Kurulu",
        "points": [
            "Explicit consent required for sensitive (health) data processing.",
            "Rights to learn, access, correct, and request erasure/deletion.",
        ],
    },
    "RU": {
        "law": "Federal Law 152-FZ 'On Personal Data'",
        "regulator": "Roskomnadzor",
        "points": [
            "Consent-based processing; special categories (health) need written consent.",
            "Right of access, clarification, blocking, and destruction.",
        ],
    },
    "ZA": {
        "law": "Protection of Personal Information Act (POPIA)",
        "regulator": "Information Regulator (South Africa)",
        "points": [
            "Health data is 'special personal information' requiring consent.",
            "Rights of access, correction, deletion, and objection.",
        ],
    },
    "MX": {
        "law": "Ley Federal de Protección de Datos Personales en Posesión de los Particulares (as amended 2025 framework)",
        "regulator": "Secretaría de Anticorrupción y Buen Gobierno (data protection authority)",
        "points": [
            "ARCO rights: access, rectification, cancellation, opposition.",
            "Health data processing requires express consent.",
        ],
    },
    "CN": {
        "law": "Personal Information Protection Law (PIPL)",
        "regulator": "Cyberspace Administration of China",
        "points": [
            "Health data is 'sensitive personal information' — separate consent required.",
            "Rights of access, copy, correction, deletion; rules on cross-border transfer apply.",
        ],
    },
    "GEN": {
        "law": "General data-protection principles",
        "regulator": "your national data-protection authority",
        "points": [
            "We apply the strictest common baseline everywhere: notice, consent, access, correction, erasure.",
            "Country-specific statutes are added as we verify them — ask us if yours is missing.",
        ],
    },
}


def notes_for_country(country_code: str | None) -> dict:
    key = REGIME_BY_COUNTRY.get((country_code or "").upper(), "GEN")
    return {"region_key": key, **REGION_LEGAL_NOTES[key]}
