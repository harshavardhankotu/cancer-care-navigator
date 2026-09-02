from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class FamilyCreate(BaseModel):
    email: str
    password: str
    consent_accepted: bool = False  # DPDP Act 2023 — must be explicitly accepted
    country: str | None = None


class TokenOut(BaseModel):
    token: str
    email: str


class CaseCreate(BaseModel):
    patient_name: str = Field(min_length=1)
    cancer_type: str = Field(min_length=1)
    patient_age: int | None = Field(default=None, ge=0, le=130)
    patient_sex: Literal["female", "male", "other", "unknown"] | None = None
    stage: str | None = None
    diagnosis_date: date | None = None
    current_status: str | None = None
    country: str | None = None


class CaseUpdate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=1)
    cancer_type: str | None = Field(default=None, min_length=1)
    patient_age: int | None = Field(default=None, ge=0, le=130)
    patient_sex: Literal["female", "male", "other", "unknown"] | None = None
    stage: str | None = None
    diagnosis_date: date | None = None
    current_status: str | None = None
    country: str | None = None


class CaseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    patient_name: str
    patient_age: int | None
    patient_sex: str | None
    cancer_type: str
    stage: str | None
    diagnosis_date: date | None
    current_status: str | None
    country: str | None = None
    created_at: datetime


class DocumentPatch(BaseModel):
    extracted_date: date | None = None
    extracted_source: str | None = None
    extracted_doc_type: str | None = None
    extracted_key_findings: list[str] | None = None


class DocumentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    case_id: int
    original_filename: str | None
    uploaded_at: datetime
    extracted_date: date | None
    extracted_source: str | None
    extracted_doc_type: str | None
    extracted_key_findings: list[str] | None
    raw_extraction_json: dict | None
    has_file: bool = False


class DoctorOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    credentials: str | None
    hospital: str | None
    specialty_tags: list[str] | None
    stage_focus: list[str] | None
    contact_channel: str | None
    accepts_remote_case_review: bool
    verified_by: str | None
    last_verified_date: date | None
    avg_response_time_days: int | None


class OpinionCreate(BaseModel):
    doctor_ids: list[int]


class OpinionRespond(BaseModel):
    opinion_recommended_modality: str | None = None
    opinion_sequencing_note: str | None = None
    opinion_caveats: str | None = None
    opinion_requested_tests: str | None = None


class OpinionAction(BaseModel):
    action: Literal["mark_sent", "acknowledge", "respond", "decline", "no_response"]
    response: OpinionRespond | None = None


class OpinionOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    case_id: int
    doctor_id: int
    status: str
    case_package_version_id: int | None
    sent_at: datetime | None
    sla_deadline: datetime | None
    responded_at: datetime | None
    opinion_recommended_modality: str | None
    opinion_sequencing_note: str | None
    opinion_caveats: str | None
    opinion_requested_tests: str | None
    conflicts_flagged: bool


class PackageOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    case_id: int
    version_number: int
    snapshot_json: dict
    generated_at: datetime


class FlagOut(BaseModel):
    id: int
    case_id: int
    flag_type: str
    message: str | None
    triggered_at: datetime
    acknowledged: bool
    acknowledged_at: datetime | None
    rule: dict | None = None


class CenterOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    location: str | None
    capabilities: list[str] | None
    cancer_types: list[str] | None
    verified_by: str | None
    last_verified_date: date | None
    country: str | None = None
    website: str | None = None


class WaitReportIn(BaseModel):
    center_name: str = Field(min_length=1, max_length=255)
    reported_wait_days: int = Field(ge=0, le=400)


class TransferIn(BaseModel):
    from_hospital: str | None = None
    to_hospital: str | None = None


class TransferOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    case_id: int
    from_hospital: str | None
    to_hospital: str | None
    status: str
    requested_at: datetime


class TrialOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    source: str
    external_id: str
    title: str
    cancer_types: list[str] | None
    biomarkers: list[str] | None
    location: str | None
    status: str | None
    url: str | None


class FinProfileIn(BaseModel):
    insurance_status: Literal[
        "uninsured", "private_insured", "employer_group",
        "government_scheme", "unknown"
    ] | None = None
    insurer_name: str | None = None
    income_bracket: Literal[
        "low", "lower_middle", "middle", "upper_middle", "high", "unknown"
    ] | None = None
    budget_ceiling: float | None = Field(default=None, ge=0)


class FinProfileOut(FinProfileIn):
    model_config = {"from_attributes": True}
    id: int
    case_id: int


class CoverageCheckIn(BaseModel):
    country: str | None = None
    insurance_status: Literal[
        "uninsured", "private_insured", "employer_group",
        "government_scheme", "unknown"
    ] = "uninsured"
    income_bracket: Literal[
        "low", "lower_middle", "middle", "upper_middle", "high", "unknown"
    ] = "unknown"
    employment: Literal[
        "central_government_employee", "central_government_pensioner",
        "state_government", "private_sector", "informal_sector", "other",
        "retired_senior", "unemployed", "unknown"
    ] = "unknown"
