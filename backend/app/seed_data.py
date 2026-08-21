"""Seed data for the Cancer Care Navigator MVP.

CONTENT PROVENANCE:
- foreclosure_rules: real, citable guideline-based sequencing risks (simplified
  summaries). A clinician must review wording before production use.
- specialist_centers: real, well-known Indian cancer centres with publicly
  documented capabilities. STARTER LIST — requires ongoing manual verification.
- doctors: PLACEHOLDER role-level entries. NOT real individuals.
- trials: PLACEHOLDER example records pending CTRI/ClinicalTrials.gov API work.
- coverage_schemes: PM-JAY and CGHS described at the level of public general
  information; parameters change — verify before relying on them.
- patient_assistance_programs: realistic PLACEHOLDER examples.

Everything seeded here is marked so the UI can badge it as
"unverified / example data".
"""

from datetime import date

TODAY = date.today()
SEED_MARK = "seed-starter-list (requires manual verification)"
PLACEHOLDER = "PLACEHOLDER - not verified"

FORECLOSURE_RULES = [
    {
        "id": 1,
        "condition_description": (
            "Systemic steroids started before a diagnostic biopsy in suspected lymphoma "
            "(steroids can lyse lymphoma cells and render tissue non-diagnostic)."
        ),
        "foreclosed_option": "Accurate histopathological diagnosis and subtype classification, "
                             "which determines the entire treatment pathway.",
        "source_guideline": "Standard haemato-oncology practice guidance",
        "source_citation": "BCSH/BSH guideline on the management of lymphoma; widely documented "
                           "practice point that corticosteroids prior to biopsy may preclude diagnosis.",
        "cancer_types": ["lymphoma", "hodgkin"],
    },
    {
        "id": 2,
        "condition_description": (
            "Definitive (chemo)radiation initiated in advanced non-squamous NSCLC before "
            "EGFR/ALK/ROS1/PD-L1 molecular testing results are available."
        ),
        "foreclosed_option": "First-line targeted therapy (e.g., osimertinib for EGFR-mutant disease), "
                             "which is standard-of-care ahead of cytotoxic chemotherapy when a driver "
                             "mutation is present.",
        "source_guideline": "NCCN Clinical Practice Guidelines in Oncology: Non-Small Cell Lung Cancer",
        "source_citation": "NCCN NSCLC Guidelines recommend broad molecular profiling before starting "
                           "systemic or definitive local therapy in non-squamous NSCLC.",
        "cancer_types": ["non-small cell lung cancer", "nsclc", "lung adenocarcinoma"],
    },
    {
        "id": 3,
        "condition_description": (
            "Unplanned excision or enucleation biopsy ('whoops procedure') of a suspected "
            "soft-tissue sarcoma at a referring/local hospital instead of referral before biopsy."
        ),
        "foreclosed_option": "Limb-sparing wide resection with clean margins; tumour seeding along the "
                             "biopsy tract often forces wider re-excision.",
        "source_guideline": "NCCN Clinical Practice Guidelines in Oncology: Soft Tissue Sarcoma",
        "source_citation": "NCCN Soft Tissue Sarcoma Guidelines: biopsy should be planned by the treating "
                           "sarcoma team before any excision; improperly placed biopsy compromises "
                           "limb-salvage surgery.",
        "cancer_types": ["soft tissue sarcoma"],
    },
    {
        "id": 4,
        "condition_description": (
            "Biopsy of a suspected primary bone tumour (e.g., osteosarcoma, Ewing sarcoma) performed "
            "at a centre other than the one performing definitive surgery."
        ),
        "foreclosed_option": "Limb-salvage surgery; a poorly placed biopsy tract may require wider "
                             "resection of bone/soft tissue or amputation.",
        "source_guideline": "Established orthopaedic oncology principle",
        "source_citation": "Mankin HJ et al., 'The hazards of the biopsy, revisited' (J Bone Joint Surg Am, "
                           "1996); reflected in ESMO/EURAMOS osteosarcoma guidance: biopsy at the definitive "
                           "treatment centre.",
        "cancer_types": ["osteosarcoma", "ewing sarcoma", "bone tumor", "bone tumour"],
    },
    {
        "id": 5,
        "condition_description": (
            "Gonadotoxic chemotherapy or pelvic radiation started without fertility-preservation "
            "counselling in a patient of reproductive age (<=45)."
        ),
        "foreclosed_option": "Future biological fertility (sperm/oocyte/embryo/ovarian-tissue preservation "
                             "must happen BEFORE gonadotoxic therapy starts).",
        "source_guideline": "ASCO Clinical Practice Guideline: Fertility Preservation in Patients With Cancer",
        "source_citation": "Oktay K et al., J Clin Oncol 2018;36:1994-2001. As soon as possible after "
                           "diagnosis, providers should discuss fertility preservation options.",
        "cancer_types": ["any"],
    },
    {
        "id": 6,
        "condition_description": (
            "Up-front surgery chosen for stage II-III triple-negative or HER2-positive breast cancer "
            "instead of neoadjuvant systemic therapy."
        ),
        "foreclosed_option": "Response-adapted treatment: pathological complete response after neoadjuvant "
                             "therapy guides prognosis and adjuvant decisions, and can enable less extensive "
                             "surgery.",
        "source_guideline": "NCCN Clinical Practice Guidelines in Oncology: Breast Cancer",
        "source_citation": "NCCN Breast Cancer Guidelines list neoadjuvant systemic therapy as preferred "
                           "initial treatment for operable stage II-III TNBC and HER2-positive disease.",
        "cancer_types": ["breast"],
    },
    {
        "id": 7,
        "condition_description": (
            "Anti-EGFR antibody therapy (cetuximab/panitumumab) started in metastatic colorectal cancer "
            "before extended RAS (KRAS/NRAS) testing results are available."
        ),
        "foreclosed_option": "An effective first-line biologic choice: anti-EGFR therapy is ineffective and "
                             "harmful in RAS-mutant disease, wasting time and toxicity on a foregone option.",
        "source_guideline": "NCCN Clinical Practice Guidelines in Oncology: Colon Cancer / Rectal Cancer",
        "source_citation": "NCCN Colon/Rectal Cancer Guidelines require extended RAS mutation testing "
                           "(and HER2/BRAF where relevant) before anti-EGFR antibody selection in metastatic "
                           "disease.",
        "cancer_types": ["colorectal", "colon", "rectal"],
    },
    {
        "id": 8,
        "condition_description": (
            "Radiation-only local therapy decided for an operable early oral-cavity or laryngeal cancer "
            "without a documented multidisciplinary discussion of the surgical alternative."
        ),
        "foreclosed_option": "Informed organ-preservation trade-off: surgery-first keeps radiation in reserve "
                             "for salvage; RT-only forecloses easy salvage if the tumour is radioresistant.",
        "source_guideline": "NCCN Clinical Practice Guidelines in Oncology: Head and Neck Cancers",
        "source_citation": "NCCN Head and Neck Cancers Guidelines emphasise multidisciplinary evaluation "
                           "before selecting single-modality local therapy in early-stage disease.",
        "cancer_types": ["oral cavity", "larynx", "laryngeal", "oropharyn", "head and neck"],
    },
]

SPECIALIST_CENTERS = [
    {"name": "Tata Memorial Centre (TMH)", "location": "Parel, Mumbai, Maharashtra",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "HIPEC",
                      "pediatric oncology", "thoracic surgical oncology", "head & neck surgical oncology",
                      "PET-CT", "palliative care", "National Cancer Grid lead"],
     "cancer_types": ["any"]},
    {"name": "Dr. B.R.A. Institute Rotary Cancer Hospital, AIIMS New Delhi", "location": "Ansari Nagar, New Delhi",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "pediatric oncology",
                      "radiation therapy (LINAC + brachytherapy)", "surgical oncology", "medical oncology"],
     "cancer_types": ["any"]},
    {"name": "Cancer Institute (WIA), Adyar", "location": "Adyar, Chennai, Tamil Nadu",
     "capabilities": ["comprehensive cancer centre", "radiation therapy", "pediatric oncology",
                      "preventive oncology screening", "subsidised/free care programmes"],
     "cancer_types": ["any"]},
    {"name": "Basavatarakam Indo-American Cancer Hospital & Research Institute", "location": "Banjara Hills, Hyderabad, Telangana",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "surgical oncology",
                      "radiation therapy", "medical oncology"],
     "cancer_types": ["any"]},
    {"name": "Apollo Proton Cancer Centre", "location": "Tharamani, Chennai, Tamil Nadu",
     "capabilities": ["proton beam therapy (first in South Asia)", "radiation therapy",
                      "surgical oncology", "medical oncology"],
     "cancer_types": ["any"]},
    {"name": "Rajiv Gandhi Cancer Institute & Research Centre", "location": "Rohini, New Delhi",
     "capabilities": ["comprehensive cancer centre", "robotic surgery", "bone marrow transplant",
                      "radiation therapy"],
     "cancer_types": ["any"]},
    {"name": "Regional Cancer Centre, PGIMER", "location": "Chandigarh",
     "capabilities": ["public regional cancer centre", "bone marrow transplant", "pediatric oncology",
                      "radiation therapy"],
     "cancer_types": ["any"]},
    {"name": "Kidwai Memorial Institute of Oncology", "location": "Bengaluru, Karnataka",
     "capabilities": ["public regional cancer centre", "affordable care", "radiation therapy",
                      "surgical oncology"],
     "cancer_types": ["any"]},
]

# Objective, citable public facts — the raw material for transparent hospital
# comparison. Every entry carries a source URL the patient can check directly.
# We deliberately do NOT aggregate user reviews ("bought reviews" problem) and we
# do NOT rank individual doctors.
NABH_DIR = "https://nabh.co/find-a-healthcare-organisation/"
PMJAY_FIND = "https://hospitals.pmjay.gov.in/Search/empnlWorkFlow.htm?actionFlag=ViewRegisteredHosptlsNew"
PMJAY_DEEMP = "https://snomedct.abdm.gov.in/hospital/de-empanelled"

HOSPITAL_NOTES = [
    {"center_name": "Tata Memorial Centre (TMH)", "note_type": "ownership",
     "detail": "Public-funded institution under the Department of Atomic Energy, Government of India.",
     "source_name": "tmc.gov.in", "source_url": "https://tmc.gov.in/"},
    {"center_name": "Tata Memorial Centre (TMH)", "note_type": "accreditation",
     "detail": "Long-standing national accreditation; verify current status in the public NABH directory.",
     "source_name": "NABH public directory", "source_url": NABH_DIR},
    {"center_name": "Tata Memorial Centre (TMH)", "note_type": "scheme_empanelment",
     "detail": "Searchable in the official PM-JAY empanelled-hospital portal (cashless treatment for eligible beneficiaries).",
     "source_name": "NHA PM-JAY Find-Hospital", "source_url": PMJAY_FIND},

    {"center_name": "Dr. B.R.A. Institute Rotary Cancer Hospital, AIIMS New Delhi", "note_type": "ownership",
     "detail": "Part of AIIMS New Delhi, an Institute of National Importance under the Ministry of Health & Family Welfare.",
     "source_name": "aiims.edu", "source_url": "https://www.aiims.edu/"},
    {"center_name": "Dr. B.R.A. Institute Rotary Cancer Hospital, AIIMS New Delhi", "note_type": "accreditation",
     "detail": "AIIMS New Delhi facilities have held national accreditation; verify current scope in the NABH directory.",
     "source_name": "NABH public directory", "source_url": NABH_DIR},

    {"center_name": "Cancer Institute (WIA), Adyar", "note_type": "ownership",
     "detail": "Non-profit autonomous institution, state-aided; known historically for subsidised/free cancer care.",
     "source_name": "cancerinstitutewia.in", "source_url": "https://www.cancerinstitutewia.in/"},
    {"center_name": "Cancer Institute (WIA), Adyar", "note_type": "accreditation",
     "detail": "Verify current accreditation status in the public NABH directory.",
     "source_name": "NABH public directory", "source_url": NABH_DIR},

    {"center_name": "Basavatarakam Indo-American Cancer Hospital & Research Institute", "note_type": "ownership",
     "detail": "Run by a charitable trust (non-profit model).",
     "source_name": "basavatarakam.org", "source_url": "https://basavatarakam.org/"},

    {"center_name": "Apollo Proton Cancer Centre", "note_type": "ownership",
     "detail": "Corporate hospital group (Apollo Hospitals Enterprise Ltd., a listed company). Ownership type matters: corporate chains have commercial incentives patients should weigh alongside quality indicators.",
     "source_name": "apollohospitals.com investor page", "source_url": "https://www.apollohospitals.com/investors/"},
    {"center_name": "Apollo Proton Cancer Centre", "note_type": "accreditation",
     "detail": "Apollo group facilities have held NABH and JCI accreditations; verify THIS unit's current status in the directories.",
     "source_name": "NABH public directory", "source_url": NABH_DIR},

    {"center_name": "Rajiv Gandhi Cancer Institute & Research Centre", "note_type": "ownership",
     "detail": "Managed by a registered not-for-profit society.",
     "source_name": "rgcirc.org", "source_url": "https://www.rgcirc.org/"},
    {"center_name": "Rajiv Gandhi Cancer Institute & Research Centre", "note_type": "accreditation",
     "detail": "Has publicly reported national accreditation; verify current status in the NABH directory.",
     "source_name": "NABH public directory", "source_url": NABH_DIR},

    {"center_name": "Regional Cancer Centre, PGIMER", "note_type": "ownership",
     "detail": "PGIMER is an Institute of National Importance (central government); the Regional Cancer Centre sits within it.",
     "source_name": "pgimer.edu.in", "source_url": "https://pgimer.edu.in/"},
    {"center_name": "Regional Cancer Centre, PGIMER", "note_type": "scheme_empanelment",
     "detail": "Public teaching hospitals typically participate in central/state health schemes; confirm on PM-JAY portal.",
     "source_name": "NHA PM-JAY Find-Hospital", "source_url": PMJAY_FIND},

    {"center_name": "Kidwai Memorial Institute of Oncology", "note_type": "ownership",
     "detail": "Government of Karnataka-run regional cancer centre with subsidised care mandate.",
     "source_name": "Karnataka Health Dept.", "source_url": "https://karunadu.karnataka.gov.in/hfw/kidwai"},
    {"center_name": "Kidwai Memorial Institute of Oncology", "note_type": "scheme_empanelment",
     "detail": "Searchable in the official PM-JAY empanelled-hospital portal.",
     "source_name": "NHA PM-JAY Find-Hospital", "source_url": PMJAY_FIND},
]

# Where ANY patient can independently check ANY hospital (public knowledge,
# free access). Shown in the UI next to scores.
PUBLIC_CHECK_LINKS = [
    {"label": "Check accreditation (NABH public directory)", "url": NABH_DIR},
    {"label": "Check PM-JAY empanelment (official portal)", "url": PMJAY_FIND},
    {"label": "Check if a hospital was DE-empanelled by PM-JAY (fraud/quality actions)",
     "url": PMJAY_DEEMP},
    {"label": "Check consumer-forum cases (e-Daakhil / NCDRC case search)", "url": "https://edaakhil.nic.in/"},
    {"label": "Check doctor registration (National Medical Commission register)", "url": "https://www.nmc.org.in/information-desk/indian-medical-register/"},

]

DOCTORS = [
    {"name": "Senior Consultant, Medical Oncology (Breast & GI) [placeholder]",
     "credentials": "MD, DM (Medical Oncology)",
     "hospital": "[Large public regional cancer centre] (placeholder entry)",
     "specialty_tags": ["medical oncology", "breast", "GI"], "stage_focus": ["II", "III", "IV"],
     "contact_channel": "email via second-opinion coordinator", "contact_detail": "coordinator@example.invalid",
     "accepts_remote_case_review": True, "avg_response_time_days": 7},
    {"name": "Senior Consultant, Radiation Oncology [placeholder]",
     "credentials": "MD (Radiation Oncology)",
     "hospital": "[Large private comprehensive cancer centre] (placeholder entry)",
     "specialty_tags": ["radiation oncology"], "stage_focus": ["I", "II", "III"],
     "contact_channel": "teleconsult platform", "contact_detail": "appointments@example.invalid",
     "accepts_remote_case_review": True, "avg_response_time_days": 5},
    {"name": "Professor & Head, Surgical Oncology (Thoracic) [placeholder]",
     "credentials": "MS, MCh (Surgical Oncology)",
     "hospital": "[Teaching hospital cancer centre] (placeholder entry)",
     "specialty_tags": ["surgical oncology", "thoracic"], "stage_focus": ["I", "II", "III"],
     "contact_channel": "email", "contact_detail": "surgery-referrals@example.invalid",
     "accepts_remote_case_review": True, "avg_response_time_days": 10},
    {"name": "Consultant, Paediatric Haematology-Oncology [placeholder]",
     "credentials": "MD, Fellowship (Paediatric Oncology)",
     "hospital": "[Children's hospital cancer unit] (placeholder entry)",
     "specialty_tags": ["paediatric oncology"], "stage_focus": ["all"],
     "contact_channel": "phone via clinic nurse", "contact_detail": "+91-00000-00000 (placeholder)",
     "accepts_remote_case_review": True, "avg_response_time_days": 4},
    {"name": "Senior Consultant, Haematology & BMT [placeholder]",
     "credentials": "MD, DM (Clinical Haematology)",
     "hospital": "[Bone-marrow-transplant centre] (placeholder entry)",
     "specialty_tags": ["haematology", "BMT", "lymphoma", "leukemia"], "stage_focus": ["all"],
     "contact_channel": "email", "contact_detail": "bmt-opinions@example.invalid",
     "accepts_remote_case_review": True, "avg_response_time_days": 6},
]

TRIALS = [
    {"source": "CTRI", "external_id": "CTRI-EXAMPLE-001",
     "title": "[Example record] Phase III adjuvant therapy trial in HER2-positive early breast cancer",
     "cancer_types": ["breast"], "biomarkers": ["HER2"], "location": "Multiple centres, India",
     "status": "Recruiting (example)", "url": "https://ctri.nic.in"},
    {"source": "CTRI", "external_id": "CTRI-EXAMPLE-002",
     "title": "[Example record] Randomised study of immunotherapy in EGFR-mutated advanced lung adenocarcinoma",
     "cancer_types": ["lung", "nsclc"], "biomarkers": ["EGFR"], "location": "Delhi NCR, India",
     "status": "Recruiting (example)", "url": "https://ctri.nic.in"},
    {"source": "ClinicalTrials.gov", "external_id": "NCT-EXAMPLE-003",
     "title": "[Example record] Neoadjuvant chemoradiation vs induction chemo in locally advanced rectal cancer",
     "cancer_types": ["rectal", "colorectal"], "biomarkers": [], "location": "Multi-country incl. India sites",
     "status": "Active (example)", "url": "https://clinicaltrials.gov"},
    {"source": "CTRI", "external_id": "CTRI-EXAMPLE-004",
     "title": "[Example record] Maintenance therapy trial in BRCA-mutated relapsed ovarian cancer",
     "cancer_types": ["ovarian"], "biomarkers": ["BRCA1", "BRCA2"], "location": "Mumbai, India",
     "status": "Recruiting (example)", "url": "https://ctri.nic.in"},
    {"source": "CTRI", "external_id": "CTRI-EXAMPLE-005",
     "title": "[Example record] Adjuvant imatinib duration study in localised gastrointestinal stromal tumour",
     "cancer_types": ["gist", "sarcoma"], "biomarkers": ["KIT"], "location": "Bengaluru, India",
     "status": "Recruiting (example)", "url": "https://ctri.nic.in"},
]

COVERAGE_SCHEMES = [
    {
        "scheme_name": "Ayushman Bharat PM-JAY (Pradhan Mantri Jan Arogya Yojana)",
        "eligibility_criteria_json": {
            "summary": "Targets low-income households identified by the SECC 2011 deprivation criteria "
                       "and notified occupational categories. No contribution. Check beneficiary status "
                       "on the official PM-JAY portal or at any empanelled hospital's Ayushman desk.",
            "checks": [
                {"field": "insurance_status", "op": "not_in", "value": ["private_insured", "employer_group"]},
                {"field": "employment", "op": "not_in", "value": ["central_government_employee", "central_government_pensioner"]},
                {"field": "income_bracket", "op": "in_or_unknown", "value": ["low", "lower_middle"]},
            ],
        },
        "covered_treatments": ["secondary care hospitalisation", "tertiary care hospitalisation",
                               "chemotherapy packages", "major surgeries incl. cancer resections",
                               "radiation therapy packages", "diagnostics during admission"],
        "network_hospitals": ["Tata Memorial Centre (Mumbai)", "AIIMS New Delhi",
                              "Kidwai Memorial Institute of Oncology (Bengaluru)",
                              "Regional Cancer Centre PGIMER (Chandigarh)"],
        "coverage_limit": "Rs. 5,00,000 per family per year (secondary + tertiary care)",
        "exclusions": ["OPD consultations and outpatient medicines (generally)",
                       "cosmetic/aesthetic procedures", "fertility/IVF treatment",
                       "self-inflicted injuries", "individuals/families already covered by similar government plans"],
        "last_verified_date": TODAY,
    },
    {
        "scheme_name": "CGHS (Central Government Health Scheme)",
        "eligibility_criteria_json": {
            "summary": "For serving Central Government employees, pensioners and their dependent family "
                       "members; fixed contribution by pay level. Covers OPD + IPD including cancer "
                       "treatment at CGHS rates in empanelled hospitals.",
            "checks": [
                {"field": "employment", "op": "in_or_unknown",
                 "value": ["central_government_employee", "central_government_pensioner"]},
            ],
        },
        "covered_treatments": ["OPD consultations", "investigations", "chemotherapy drugs (CGHS rates)",
                               "surgery", "radiotherapy", "hospitalisation at empanelled hospitals"],
        "network_hospitals": ["Empanelled private hospitals per city (see CGHS empanelment list)",
                              "Central government hospitals"],
        "coverage_limit": "As per CGHS entitlement norms (ward entitlement by pay level)",
        "exclusions": ["procedures not on the CGHS approved list require prior approval",
                       "private/upgraded ward differences are out-of-pocket"],
        "last_verified_date": TODAY,
    },
    {
        "scheme_name": "State cancer-care schemes (e.g., MJPJAY Maharashtra / Aarogyasri Telangana & AP / CMCHIS Tamil Nadu)",
        "eligibility_criteria_json": {
            "summary": "Most large states run cashless tertiary-care schemes for low-income families "
                       "(income/BPL criteria vary by state). Verify current income thresholds and "
                       "empanelled hospitals on the respective state trust portal.",
            "checks": [
                {"field": "insurance_status", "op": "not_in", "value": ["private_insured", "employer_group"]},
                {"field": "income_bracket", "op": "in_or_unknown", "value": ["low", "lower_middle"]},
            ],
        },
        "covered_treatments": ["cashless tertiary care incl. cancer procedures at empanelled hospitals"],
        "network_hospitals": ["state-specific empanelled lists (verify on state portal)"],
        "coverage_limit": "Varies by state scheme",
        "exclusions": ["varies by state; typically OPD and certain high-end implants"],
        "last_verified_date": TODAY,
    },
]

PATIENT_ASSISTANCE_PROGRAMS = [
    {"drug_name": "Imatinib mesylate (generic)", "manufacturer": "[Generic manufacturer] (placeholder example)",
     "program_type": "free-drug programme for eligible low-income patients (placeholder example)",
     "eligibility_criteria": "Documented CML/GIST diagnosis; household income below stated threshold; Indian resident. PLACEHOLDER - verify with manufacturer.",
     "application_process": "Apply via treating haematologist/oncologist with income proof and prescription. PLACEHOLDER - verify current process.",
     "verified_by": PLACEHOLDER, "last_verified_date": TODAY},
    {"drug_name": "Trastuzumab (biosimilar)", "manufacturer": "[Biosimilar marketer] (placeholder example)",
     "program_type": "discounted vial programme via hospital pharmacy (placeholder example)",
     "eligibility_criteria": "HER2-positive diagnosis confirmed by IHC/FISH; treated at participating hospital. PLACEHOLDER - verify.",
     "application_process": "Hospital pharmacy enrolment form signed by treating oncologist. PLACEHOLDER - verify.",
     "verified_by": PLACEHOLDER, "last_verified_date": TODAY},
]
