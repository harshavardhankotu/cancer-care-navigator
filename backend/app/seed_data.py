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
    {"country": "IN", "name": "Tata Memorial Centre (TMH)", "location": "Parel, Mumbai, Maharashtra",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "HIPEC",
                      "pediatric oncology", "thoracic surgical oncology", "head & neck surgical oncology",
                      "PET-CT", "palliative care", "National Cancer Grid lead"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Dr. B.R.A. Institute Rotary Cancer Hospital, AIIMS New Delhi", "location": "Ansari Nagar, New Delhi",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "pediatric oncology",
                      "radiation therapy (LINAC + brachytherapy)", "surgical oncology", "medical oncology"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Cancer Institute (WIA), Adyar", "location": "Adyar, Chennai, Tamil Nadu",
     "capabilities": ["comprehensive cancer centre", "radiation therapy", "pediatric oncology",
                      "preventive oncology screening", "subsidised/free care programmes"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Basavatarakam Indo-American Cancer Hospital & Research Institute", "location": "Banjara Hills, Hyderabad, Telangana",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "surgical oncology",
                      "radiation therapy", "medical oncology"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Apollo Proton Cancer Centre", "location": "Tharamani, Chennai, Tamil Nadu",
     "capabilities": ["proton beam therapy (first in South Asia)", "radiation therapy",
                      "surgical oncology", "medical oncology"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Rajiv Gandhi Cancer Institute & Research Centre", "location": "Rohini, New Delhi",
     "capabilities": ["comprehensive cancer centre", "robotic surgery", "bone marrow transplant",
                      "radiation therapy"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Regional Cancer Centre, PGIMER", "location": "Chandigarh",
     "capabilities": ["public regional cancer centre", "bone marrow transplant", "pediatric oncology",
                      "radiation therapy"],
     "cancer_types": ["any"]},
    {"country": "IN", "name": "Kidwai Memorial Institute of Oncology", "location": "Bengaluru, Karnataka",
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

# =====================================================================
# GLOBAL EXPANSION (v0.3) — worldwide centres, schemes, assistance
# Every fact below is objective and publicly citable; every centre entry
# carries notes with sources. Starter list — verify before relying.
# =====================================================================

NCI_LIST = "https://www.cancer.gov/research/infrastructure/cancer-centers/find"
JCI = "https://www.jointcommissioninternational.org/"
NHS_UK = "https://www.nhs.uk/"

def _nci_comprehensive():
    return {"note_type": "designation",
            "detail": "NCI-Designated Comprehensive Cancer Center — the U.S. National Cancer Institute's highest designation, awarded against published criteria (research breadth, patient volume, prevention & community outreach).",
            "source_name": "NCI cancer centers list", "source_url": NCI_LIST}

def _jci_note():
    return {"note_type": "accreditation",
            "detail": "Held JCI accreditation — verify current status in the JCI directory.",
            "source_name": "Joint Commission International", "source_url": JCI}

WORLD_CENTERS = [
    {"country": "US", "name": "MD Anderson Cancer Center", "location": "Houston, Texas",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "proton therapy",
                      "pediatric oncology", "immunotherapy trials"],
     "cancer_types": ["any"],
     "notes": [_nci_comprehensive(),
               {"note_type": "ownership", "detail": "Public: University of Texas System.",
                "source_name": "mdanderson.org", "source_url": "https://www.mdanderson.org/"}, _jci_note()]},

    {"country": "US", "name": "Memorial Sloan Kettering Cancer Center", "location": "New York, NY",
     "capabilities": ["comprehensive cancer centre", "bone marrow transplant", "pediatric oncology",
                      "robotic surgery"],
     "cancer_types": ["any"],
     "notes": [_nci_comprehensive(),
               {"note_type": "ownership", "detail": "Nonprofit hospital chartered by New York State.",
                "source_name": "mskcc.org", "source_url": "https://www.mskcc.org/"}]},

    {"country": "US", "name": "Dana-Farber Cancer Institute", "location": "Boston, MA",
     "capabilities": ["comprehensive cancer centre", "pediatric oncology", "bone marrow transplant"],
     "cancer_types": ["any"],
     "notes": [_nci_comprehensive(),
               {"note_type": "ownership", "detail": "Nonprofit teaching affiliate of Harvard Medical School.",
                "source_name": "dana-farber.org", "source_url": "https://www.dana-farber.org/"}]},

    {"country": "US", "name": "Mayo Clinic Cancer Center", "location": "Rochester, MN (+AZ, FL)",
     "capabilities": ["comprehensive cancer centre", "proton therapy", "multidisciplinary care"],
     "cancer_types": ["any"],
     "notes": [_nci_comprehensive(),
               {"note_type": "ownership", "detail": "Nonprofit academic medical center.",
                "source_name": "mayoclinic.org", "source_url": "https://www.mayoclinic.org/"}]},

    {"country": "GB", "name": "The Royal Marsden NHS Foundation Trust", "location": "London & Sutton",
     "capabilities": ["comprehensive cancer centre", "robotic surgery", "clinical trials unit",
                      "private patients unit"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "World's first hospital dedicated to cancer treatment (opened 1851); leading NHS specialist trust with the Institute of Cancer Research.",
                "source_name": "royalmarsden.nhs.uk", "source_url": "https://www.royalmarsden.nhs.uk/"},
               {"note_type": "ownership", "detail": "Public: NHS Foundation Trust.",
                "source_name": NHS_UK, "source_url": NHS_UK},
               {"note_type": "scheme_empanelment",
                "detail": "Care free at point of use for eligible UK residents under the NHS.",
                "source_name": NHS_UK, "source_url": NHS_UK}]},

    {"country": "GB", "name": "The Christie NHS Foundation Trust", "location": "Manchester",
     "capabilities": ["comprehensive cancer centre", "proton therapy", "radiotherapy research"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "One of Europe's leading single-site cancer centres; an NHS foundation trust with a proton-beam facility.",
                "source_name": "christies.org", "source_url": "https://www.christies.org/"},
               {"note_type": "ownership", "detail": "Public: NHS Foundation Trust.",
                "source_name": NHS_UK, "source_url": NHS_UK}]},

    {"country": "CA", "name": "Princess Margaret Cancer Centre", "location": "Toronto, Ontario",
     "capabilities": ["comprehensive cancer centre", "radiation medicine", "immunotherapy trials"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Canada's largest dedicated cancer centre, part of University Health Network.",
                "source_name": "uhn.ca / theprincessmargaret.ca", "source_url": "https://www.uhn.ca/"},
               {"note_type": "ownership", "detail": "Public: University Health Network, Ontario.",
                "source_name": "uhn.ca", "source_url": "https://www.uhn.ca/"}]},

    {"country": "CA", "name": "BC Cancer Vancouver Centre", "location": "Vancouver, British Columbia",
     "capabilities": ["provincial cancer agency", "screening programmes", "systemic therapy"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Public provincial agency (BC Cancer, Provincial Health Services Authority).",
                "source_name": "bcancer.bc.ca", "source_url": "http://www.bccancer.bc.ca/"}]},

    {"country": "AU", "name": "Peter MacCallum Cancer Centre", "location": "Melbourne, Victoria",
     "capabilities": ["comprehensive cancer centre", "radiation therapy", "bone marrow transplant"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Australia's only public hospital solely dedicated to cancer treatment, research and education.",
                "source_name": "petermac.org", "source_url": "https://www.petermac.org/"},
               {"note_type": "ownership", "detail": "Public: Victorian state government health service.",
                "source_name": "petermac.org", "source_url": "https://www.petermac.org/"}]},

    {"country": "DE", "name": "Charité Comprehensive Cancer Center", "location": "Berlin",
     "capabilities": ["university hospital cancer centre", "all tumour sites", "clinical trials"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Certified Comprehensive Cancer Centre in the German Cancer Society (DKG) network; Charité is one of Europe's largest university hospitals.",
                "source_name": "ccc.charite.de", "source_url": "https://ccc.charite.de/"},
               {"note_type": "ownership", "detail": "Public university hospital (Charité).",
                "source_name": "charite.de", "source_url": "https://www.charite.de/"}]},

    {"country": "DE", "name": "National Center for Tumor Diseases (NCT) Heidelberg", "location": "Heidelberg",
     "capabilities": ["comprehensive oncology centre", "translational research", "early trials"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Flagship site of the German Cancer Consortium (DKTK); partner of German Cancer Research Center (DKFZ).",
                "source_name": "nct-heidelberg.de", "source_url": "https://www.nct-heidelberg.de/"}]},

    {"country": "NL", "name": "Antoni van Leeuwenhoek — Netherlands Cancer Institute", "location": "Amsterdam",
     "capabilities": ["dedicated national cancer institute", "research hospital"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "The Netherlands' national dedicated cancer institute combining hospital and research under one roof.",
                "source_name": "nki.nl", "source_url": "https://www.nki.nl/"}]},

    {"country": "IT", "name": "European Institute of Oncology (IEO)", "location": "Milan",
     "capabilities": ["oncology hospital", "breast programme", "clinical research"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "OECI-accredited oncology institute; part of IRCCS research network.",
                "source_name": "oeci.eu", "source_url": "https://www.oeci.eu/"},
               {"note_type": "ownership", "detail": "Private non-profit scientific institute.",
                "source_name": "ieo.it", "source_url": "https://www.ieo.it/"}]},

    {"country": "FR", "name": "Gustave Roussy", "location": "Villejuif, Paris region",
     "capabilities": ["comprehensive cancer centre", "pediatric oncology", "early-phase trials"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "France's largest cancer institute; a public-university hospital group and leading European oncology centre.",
                "source_name": "gustaveroussy.fr", "source_url": "https://www.gustaveroussy.fr/en"},
               {"note_type": "ownership", "detail": "Public: EPIC health establishment linked to Paris-Saclay University.",
                "source_name": "gustaveroussy.fr", "source_url": "https://www.gustaveroussy.fr/en"}]},

    {"country": "FR", "name": "Institut Curie", "location": "Paris",
     "capabilities": ["hospital group + research centre", "radiotherapy", "pediatric oncology"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Non-profit foundation (founded by Marie Curie's institute lineage) combining care and research.",
                "source_name": "curie.fr", "source_url": "https://institut-curie.org/"}]},

    {"country": "JP", "name": "National Cancer Center Hospital", "location": "Tokyo (Tsukiji)",
     "capabilities": ["national flagship cancer centre", "clinical trials (JCOG)", "EPOF care"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Core hospital of Japan's National Cancer Center agency under the Ministry of Health, Labour and Welfare.",
                "source_name": "ncc.go.jp", "source_url": "https://www.ncc.go.jp/en/"},
               {"note_type": "ownership", "detail": "Public national agency hospital.",
                "source_name": "ncc.go.jp", "source_url": "https://www.ncc.go.jp/en/"}]},

    {"country": "KR", "name": "National Cancer Center Korea", "location": "Goyang, Gyeonggi",
     "capabilities": ["national flagship cancer centre", "research institute", "cancer control policy"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Korea's national cancer centre established by special law; runs the national cancer control programme.",
                "source_name": "ncc.re.kr", "source_url": "https://www.ncc.re.kr/english/index.do"},
               {"note_type": "ownership", "detail": "Public government-invested institute.",
                "source_name": "ncc.re.kr", "source_url": "https://www.ncc.re.kr/english/index.do"}]},

    {"country": "SG", "name": "National Cancer Centre Singapore", "location": "Outram, Singapore",
     "capabilities": ["national flagship cancer centre", "medical oncology", "trials unit"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Singapore's national and regional referral cancer centre within SingHealth cluster.",
                "source_name": "nccs.com.sg", "source_url": "https://www.nccs.com.sg/"},
               {"note_type": "ownership", "detail": "Public healthcare cluster (SingHealth).",
                "source_name": "singhealth.com.sg", "source_url": "https://www.singhealth.com.sg/"}]},

    {"country": "CN", "name": "National Cancer Center / Cancer Hospital CAMS", "location": "Beijing (also Shenzhen)",
     "capabilities": ["national flagship cancer centre", "biobank", "registry leadership"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "China's National Cancer Center, based at the Cancer Hospital of the Chinese Academy of Medical Sciences; leads national cancer statistics.",
                "source_name": "cicams.ac.cn", "source_url": "http://www.cicams.ac.cn/"},
               {"note_type": "ownership", "detail": "Public national institution.",
                "source_name": "cicams.ac.cn", "source_url": "http://www.cicams.ac.cn/"}]},

    {"country": "BR", "name": "Instituto Nacional de Câncer (INCA)", "location": "Rio de Janeiro",
     "capabilities": ["national flagship cancer centre", "public system coordination", "tobacco control"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Brazil's federal National Cancer Institute; coordinates national cancer policy and SUS oncology networks.",
                "source_name": "gov.br/inca", "source_url": "https://www.gov.br/inca/pt-br"},
               {"note_type": "ownership", "detail": "Public federal institution.",
                "source_name": "gov.br/inca", "source_url": "https://www.gov.br/inca/pt-br"}]},

    {"country": "BR", "name": "A.C.Camargo Cancer Center", "location": "São Paulo",
     "capabilities": ["comprehensive cancer centre", "postgraduate teaching"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Private non-profit cancer centre; one of Latin America's best-known oncology hospitals.",
                "source_name": "accamargo.org.br", "source_url": "https://www.accamargo.org.br/"}]},

    {"country": "MX", "name": "Instituto Nacional de Cancerología (INCan)", "location": "Mexico City",
     "capabilities": ["national flagship cancer centre", "public referral care"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Mexico's National Cancer Institute; tertiary public referral centre.",
                "source_name": "gob.mx/incan", "source_url": "https://www.gob.mx/salud"},
               {"note_type": "ownership", "detail": "Public federal institute.",
                "source_name": "gob.mx/salud", "source_url": "https://www.gob.mx/salud"}]},

    {"country": "AE", "name": "Cleveland Clinic Abu Dhabi", "location": "Abu Dhabi",
     "capabilities": ["multispecialty hospital incl. oncology", "international referrals"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Operated by M42 (Abu Dhabi sovereign-backed health group) in partnership with Cleveland Clinic (US). Corporate-sovereign ownership is a neutral fact worth knowing.",
                "source_name": "clevelandclinicabudhabi.ae", "source_url": "https://www.clevelandclinicabudhabi.ae/"},
               _jci_note()]},

    {"country": "EG", "name": "National Cancer Institute, Cairo University", "location": "Cairo",
     "capabilities": ["national flagship cancer centre", "large-volume public care"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Egypt's oldest and largest public comprehensive cancer centre (founded 1950).",
                "source_name": "nci.cu.edu.eg", "source_url": "https://nci.cu.edu.eg/"},
               {"note_type": "ownership", "detail": "Public university institute (Cairo University).",
                "source_name": "cu.edu.eg", "source_url": "https://cu.edu.eg/"}]},

    {"country": "TR", "name": "Hacettepe University Cancer Institute", "location": "Ankara",
     "capabilities": ["university cancer institute", "basic oncology sciences"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Public state university hospital institute; Turkey's founding oncology institute.",
                "source_name": "hacettepe.edu.tr", "source_url": "https://www.hacettepe.edu.tr/"}]},

    {"country": "PL", "name": "Maria Sklodowska-Curie National Research Institute of Oncology", "location": "Warsaw (+ Gliwice, Kraków)",
     "capabilities": ["national flagship cancer centre", "radiotherapy research"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Poland's national oncology research institute (named for Marie Skłodowska-Curie).",
                "source_name": "pib-nio.pl", "source_url": "https://pib-nio.pl/"},
               {"note_type": "ownership", "detail": "Public state research institute.",
                "source_name": "pib-nio.pl", "source_url": "https://pib-nio.pl/"}]},

    {"country": "RU", "name": "N.N. Blokhin National Medical Research Center of Oncology", "location": "Moscow",
     "capabilities": ["national flagship cancer centre", "pediatric oncology"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "designation",
                "detail": "Russia's principal national oncology research and treatment centre.",
                "source_name": "ronc.ru", "source_url": "https://ronc.ru/"},
               {"note_type": "ownership", "detail": "Public national medical research center.",
                "source_name": "ronc.ru", "source_url": "https://ronc.ru/"}]},

    {"country": "ZA", "name": "Groote Schuur Hospital Oncology Service", "location": "Cape Town",
     "capabilities": ["public academic hospital", "UCT teaching hospital"],
     "cancer_types": ["any"],
     "notes": [{"note_type": "ownership",
                "detail": "Western Cape government tertiary academic hospital (University of Cape Town teaching hospital).",
                "source_name": "westerncape.gov.za", "source_url": "https://www.westerncape.gov.za/"}]},
]

UNIVERSAL_CHECK = []  # universal/residency-based systems match everyone filtered to that country

GLOBAL_SCHEMES = [
    {"country": "US", "scheme_name": "Medicaid (US)",
     "eligibility_criteria_json": {
        "summary": "Joint federal-state health coverage for people with low income; eligibility rules vary by state. Apply via your state Medicaid office or HealthCare.gov.",
        "checks": [
            {"field": "income_bracket", "op": "in_or_unknown", "value": ["low"]},
            {"field": "insurance_status", "op": "not_in", "value": ["private_insured", "employer_group"]},
        ]},
     "covered_treatments": ["physician services", "hospitalisation", "cancer treatment at participating providers"],
     "network_hospitals": ["state-specific provider lists (see medicaid.gov)"],
     "coverage_limit": "Varies by state",
     "exclusions": ["varies by state; some services need prior approval"],
     "last_verified_date": TODAY},

    {"country": "US", "scheme_name": "Medicare (US, age 65+ or qualifying disability)",
     "eligibility_criteria_json": {
        "summary": "Federal coverage mainly for people 65+ or with qualifying disabilities, regardless of income.",
        "checks": [
            {"field": "employment", "op": "in_or_unknown", "value": ["retired_senior"]},
        ]},
     "covered_treatments": ["hospital care (Part A)", "outpatient care (Part B)", "prescription drugs via Part D plans"],
     "network_hospitals": ["nationwide (Medicare-enrolled providers)"],
     "coverage_limit": "Standard Medicare cost-sharing rules apply",
     "exclusions": ["premiums/deductibles; some drugs outside formulary"],
     "last_verified_date": TODAY},

    {"country": "US", "scheme_name": "ACA Marketplace subsidies (US)",
     "eligibility_criteria_json": {
        "summary": "Income-based premium tax credits and plans on HealthCare.gov for people without affordable employer coverage.",
        "checks": [
            {"field": "insurance_status", "op": "not_in", "value": ["employer_group"]},
            {"field": "income_bracket", "op": "in_or_unknown", "value": ["low", "lower_middle", "middle"]},
        ]},
     "covered_treatments": ["essential health benefits incl. chemotherapy, surgery, radiation"],
     "network_hospitals": ["plan-dependent networks"],
     "coverage_limit": "Plan-dependent; out-of-pocket maximums apply",
     "exclusions": ["open-enrolment windows unless qualifying event"],
     "last_verified_date": TODAY},

    {"country": "US", "scheme_name": "Hospital charity care / financial assistance (501(r))",
     "eligibility_criteria_json": {
        "summary": "US nonprofit hospitals are legally required (IRS 501(r)) to maintain Financial Assistance Policies — ask the hospital billing office for their charity-care application before paying large bills.",
        "checks": [
            {"field": "insurance_status", "op": "not_in", "value": []},
        ]},
     "covered_treatments": ["discounts or free care at nonprofit hospitals meeting policy criteria"],
     "network_hospitals": ["each nonprofit hospital's own policy"],
     "coverage_limit": "Hospital-policy dependent",
     "exclusions": ["for-profit hospitals not covered by 501(r)"],
     "last_verified_date": TODAY},

    {"country": "GB", "scheme_name": "UK National Health Service (NHS)",
     "eligibility_criteria_json": {
        "summary": "Free at the point of use for residents, including cancer treatment and most cancer medicines (England's Cancer Drugs Fund covers some high-cost drugs). Overseas visitors may be charged — residency rules apply.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["GP and specialist care", "surgery", "chemotherapy", "radiotherapy", "most NHS-listed drugs"],
     "network_hospitals": ["All NHS trusts incl. Royal Marsden, The Christie, UCLH"],
     "coverage_limit": "No financial limit for covered care",
     "exclusions": ["England prescription charges unless exempt (free in Scotland/Wales/NI)", "overseas-visitor charges"],
     "last_verified_date": TODAY},

    {"country": "CA", "scheme_name": "Provincial health insurance (OHIP, MSP, etc.)",
     "eligibility_criteria_json": {
        "summary": "Canada's universal Medicare is provincial: residents register in their province (e.g., OHIP in Ontario). Hospital and physician cancer care covered; take-home cancer drugs may need provincial drug programmes (e.g., Ontario Trillium).",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["physician and hospital services", "cancer centre care"],
     "network_hospitals": ["provincial cancer centres (Princess Margaret, BC Cancer, etc.)"],
     "coverage_limit": "Province-dependent",
     "exclusions": ["outpatient drug costs unless covered by provincial/private plans"],
     "last_verified_date": TODAY},

    {"country": "AU", "scheme_name": "Medicare Australia + PBS",
     "eligibility_criteria_json": {
        "summary": "Universal coverage of doctor visits and public-hospital treatment; the Pharmaceutical Benefits Scheme (PBS) heavily subsidises listed cancer medicines.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["GP/specialist rebates", "public hospital treatment", "PBS-subsidised medicines"],
     "network_hospitals": ["public hospitals incl. Peter MacCallum"],
     "coverage_limit": "MBS schedule fees; safety-net thresholds reduce costs further",
     "exclusions": ["gap amounts above schedule fees unless no-gap arrangements"],
     "last_verified_date": TODAY},

    {"country": "FR", "scheme_name": "Assurance Maladie + ALD 100% (France)",
     "eligibility_criteria_json": {
        "summary": "Cancer is on France's ALD (long-term illness) list: related care is reimbursed at 100% under Assurance Maladie once ALD status is granted by your doctor.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["consultations, hospital care, chemotherapy/radiotherapy, ALD-listed related transport"],
     "network_hospitals": ["public hospitals + centres de lutte contre le cancer (Gustave Roussy, Curie...)"],
     "coverage_limit": "100% for ALD-related care",
     "exclusions": ["non-related care follows standard reimbursement"],
     "last_verified_date": TODAY},

    {"country": "DE", "scheme_name": "Statutory health insurance — GKV (Germany)",
     "eligibility_criteria_json": {
        "summary": "~90% of Germany is covered by statutory insurance (GKV); co-payments are capped (about 2% of gross income, 1% for chronically ill including many cancers).",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["hospital treatment", "oncology drugs on G-BA lists", "rehabilitation (Reha)"],
     "network_hospitals": ["contracted hospitals incl. university CCCs"],
     "coverage_limit": "Co-payment caps as above",
     "exclusions": ["select private-room upgrades etc."],
     "last_verified_date": TODAY},

    {"country": "JP", "scheme_name": "Japanese NHI + High-Cost Medical Care Benefit",
     "eligibility_criteria_json": {
        "summary": "Everyone resident in Japan has national/employee insurance; the High-Cost Medical Care Benefit (kogaku ryoyohi) caps monthly out-of-pocket costs for approved care such as cancer treatment, scaled to income.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["standard cancer therapies at insured facilities"],
     "network_hospitals": ["insured hospitals incl. National Cancer Center facilities"],
     "coverage_limit": "Monthly out-of-pocket cap (income/age dependent)",
     "exclusions": ["unapproved advanced treatments unless covered by special schemes"],
     "last_verified_date": TODAY},

    {"country": "KR", "scheme_name": "National Health Insurance (Korea) + 5-Major-Cancer support",
     "eligibility_criteria_json": {
        "summary": "Single-payer NHIS covers everyone; for the five major cancers (incl. stomach, colorectal, breast, liver, lung), patient co-payment is reduced to about 5% under a dedicated support programme.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["diagnosis, surgery, chemo/radiation for registered cancers"],
     "network_hospitals": ["NHIS-contracted hospitals incl. National Cancer Center Korea"],
     "coverage_limit": "~5% co-pay for five major cancers; general 20-60% otherwise",
     "exclusions": ["non-covered items per NHIS list"],
     "last_verified_date": TODAY},

    {"country": "SG", "scheme_name": "MediShield Life + MediSave (Singapore)",
     "eligibility_criteria_json": {
        "summary": "MediShield Life is universal basic catastrophic cover (B2/C ward classes); MediSave accounts help pay approved bills; means-tested subsidies lower premiums/costs further.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["large hospital bills incl. cancer treatment at subsidised wards"],
     "network_hospitals": ["public clusters incl. National Cancer Centre Singapore"],
     "coverage_limit": "Claim limits per condition/year",
     "exclusions": ["private-ward upgrades beyond limits without integrated plans"],
     "last_verified_date": TODAY},

    {"country": "BR", "scheme_name": "SUS (Brazil, universal public system)",
     "eligibility_criteria_json": {
        "summary": "Brazil's SUS provides free universal care including oncology via high-complexity centres (CACONs/UNACONs) and CEAF high-cost medicines lists.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["surgery, chemotherapy, radiotherapy, approved targeted medicines"],
     "network_hospitals": ["INCA + accredited CACON/UNACON network"],
     "coverage_limit": "No charge at point of care",
     "exclusions": ["waiting lists vary by region"],
     "last_verified_date": TODAY},

    {"country": "MX", "scheme_name": "Mexican public health system (IMSS-Bienestar transition)",
     "eligibility_criteria_json": {
        "summary": "Mexico is consolidating public coverage for uninsured people under IMSS-Bienestar; cancer care is provided through national institutes (e.g., INCan) and state services. Rules are in transition — verify current status.",
        "checks": UNIVERSAL_CHECK},
     "covered_treatments": ["cancer diagnosis and treatment through public network"],
     "network_hospitals": ["INCan and state public hospitals"],
     "coverage_limit": "Programme-dependent",
     "exclusions": ["system transitioning; verify entitlement"],
     "last_verified_date": TODAY},
]

GLOBAL_PAPS = [
    {"drug_name": "Multiple (access programmes)", "manufacturer": "The Max Foundation",
     "program_type": "Treatment-access programme for people with cancer in low/middle-income countries (real organisation — verify current criteria)",
     "eligibility_criteria": "Country/diagnosis/drug specific; typically via treating physician application. Verify at maxfoundation.org.",
     "application_process": "Physician-initiated enrolment via Max Access Solutions platform. Verify current process.",
     "verified_by": "public info — verify", "last_verified_date": TODAY},
    {"drug_name": "Multiple (co-pay grants)", "manufacturer": "PAN Foundation",
     "program_type": "US charitable co-pay grants by disease fund (real organisation — verify funds open)",
     "eligibility_criteria": "US residents with Medicare/part-d circumstances per fund criteria; income rules apply. Verify at panfoundation.org.",
     "application_process": "Online application via patient/advocate when a disease fund is open. Verify.",
     "verified_by": "public info — verify", "last_verified_date": TODAY},
    {"drug_name": "Multiple (co-pay grants)", "manufacturer": "HealthWell Foundation",
     "program_type": "US charitable copay/premium grants by disease fund (real organisation — verify)",
     "eligibility_criteria": "US residents, insurance status and income criteria per fund. Verify at healthwellfoundation.org.",
     "application_process": "Apply online for an open disease fund. Verify.",
     "verified_by": "public info — verify", "last_verified_date": TODAY},
]

# =====================================================================
# HIDDEN SUBSIDIES (v0.4) — real programmes most patients never hear about.
# category: rare_hidden | travel | drug_access — surfaced prominently in the UI.
# =====================================================================
HIDDEN_SUBSIDY_SCHEMES = [
    {"country": "IN", "category": "travel",
     "scheme_name": "Indian Railways 75% cancer-patient travel concession",
     "eligibility_criteria_json": {
        "summary": "Cancer patients travelling for treatment get a 75% fare concession in Mail/Express trains, and the accompanying escort gets one too. Ask at any reservation counter with your diagnosis certificate.",
        "checks": []},
     "covered_treatments": ["train tickets for treatment travel + escort"],
     "network_hospitals": [], "coverage_limit": "75% of fare",
     "exclusions": ["not applicable to premium trains like Rajdhani/Shatabdi classes where concession lists differ"],
     "last_verified_date": TODAY},

    {"country": "IN", "category": "rare_hidden",
     "scheme_name": "National Policy for Rare Diseases (India) - funding at Centres of Excellence",
     "eligibility_criteria_json": {
        "summary": "India's rare-disease policy provides financial support (up to Rs. 50 lakh) for treatment of specified rare diseases at notified Centres of Excellence. Many families never hear of it - apply through the CoE.",
        "checks": []},
     "covered_treatments": ["treatment of notified rare diseases at designated CoEs"],
     "network_hospitals": ["Notified CoEs: AIIMS Delhi, PGIMER Chandigarh, KEM Mumbai, NIMHANS Bengaluru and others"],
     "coverage_limit": "Up to Rs. 50 lakh per patient (as notified)",
     "exclusions": ["disease must be on the notified list; fund availability varies"],
     "last_verified_date": TODAY},

    {"country": "JP", "category": "rare_hidden",
     "scheme_name": "Nanbyo medical subsidy (Japan, intractable diseases)",
     "eligibility_criteria_json": {
        "summary": "Japan's Nanbyo system caps monthly co-payments for 300+ designated intractable diseases based on household income; many eligible patients are not registered. Apply at your municipal office with physician certification.",
        "checks": []},
     "covered_treatments": ["medical care costs for designated intractable diseases incl. many cancers treated as such"],
     "network_hospitals": ["designated medical care institutions nationwide"],
     "coverage_limit": "Monthly out-of-pocket cap scaled to income",
     "exclusions": ["must be certified as a designated disease"],
     "last_verified_date": TODAY},

    {"country": "AU", "category": "drug_access",
     "scheme_name": "Life Saving Drugs Program (Australia)",
     "eligibility_criteria_json": {
        "summary": "The Australian government supplies certain expensive life-saving medicines for rare diseases completely free to eligible patients - separate from the PBS. Check if your medicine is on the LSDP list.",
        "checks": []},
     "covered_treatments": ["specific orphan/expensive medicines for listed conditions"],
     "network_hospitals": ["LSDP-accessed via treating specialist"],
     "coverage_limit": "Free medicine for eligible patients",
     "exclusions": ["medicine-specific criteria apply"],
     "last_verified_date": TODAY},

    {"country": "GB", "category": "rare_hidden",
     "scheme_name": "NHS Highly Specialised Technologies & Individual Funding Requests (England)",
     "eligibility_criteria_json": {
        "summary": "Ultra-rare-disease drugs can be funded through NICE's Highly Specialised Technologies route, and individual patients can request non-routinely-funded treatments via an IFR raised by their NHS clinician.",
        "checks": []},
     "covered_treatments": ["highly specialised (often ultra-orphan) treatments; case-by-case IFR approvals"],
     "network_hospitals": ["NHS trusts via treating clinician"],
     "coverage_limit": "Case-dependent",
     "exclusions": ["requires clinician sponsorship and evidence review"],
     "last_verified_date": TODAY},

    {"country": "US", "category": "drug_access",
     "scheme_name": "NORD patient assistance programs (US rare diseases)",
     "eligibility_criteria_json": {
        "summary": "The National Organization for Rare Disorders runs medication assistance funds for many rare conditions, alongside manufacturer bridge programs. Search rarediseases.org for your diagnosis.",
        "checks": []},
     "covered_treatments": ["medication cost assistance for covered rare-disease funds"],
     "network_hospitals": [],
     "coverage_limit": "Fund-dependent",
     "exclusions": ["funds open/close periodically"],
     "last_verified_date": TODAY},

    {"country": "CA", "category": "drug_access",
     "scheme_name": "Provincial catastrophic / high-cost drug programs (e.g., Ontario Trillium)",
     "eligibility_criteria_json": {
        "summary": "Outside hospital, expensive take-home cancer drugs are covered by provincial programs (Ontario Trillium, BC PharmaCare etc.) once annual deductibles are met - applications are separate from your health card.",
        "checks": []},
     "covered_treatments": ["take-home prescription drugs after deductible"],
     "network_hospitals": [],
     "coverage_limit": "Deductible then large share of drug costs",
     "exclusions": ["province-specific rules"],
     "last_verified_date": TODAY},

    {"country": "KR", "category": "rare_hidden",
     "scheme_name": "Rare/intractable disease co-pay support (Korea)",
     "eligibility_criteria_json": {
        "summary": "Beyond the five-major-cancer programme, Korea's NHIS reduces co-payments to about 10% for registered rare/intractable diseases - registration is initiated by your doctor.",
        "checks": []},
     "covered_treatments": ["registered rare/intractable disease treatment"],
     "network_hospitals": ["NHIS-contracted institutions"],
     "coverage_limit": "~10% co-pay for registered conditions",
     "exclusions": ["registration required"],
     "last_verified_date": TODAY},
]
