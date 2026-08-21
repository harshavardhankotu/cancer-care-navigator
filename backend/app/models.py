from datetime import datetime

from sqlalchemy import (JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Family(Base):
    __tablename__ = "families"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="family")


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    patient_name: Mapped[str] = mapped_column(String(255))
    patient_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patient_sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cancer_type: Mapped[str] = mapped_column(String(255))
    stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diagnosis_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    current_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    family = relationship("Family", back_populates="cases")
    documents = relationship("Document", back_populates="case")
    flags = relationship("DecisionFlag", back_populates="case")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # null = manually entered record (no file)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extracted_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    extracted_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_doc_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_key_findings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_extraction_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    case = relationship("Case", back_populates="documents")

    @property
    def has_file(self) -> bool:
        return bool(self.file_path)


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    credentials: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hospital: Mapped[str | None] = mapped_column(String(255), nullable=True)
    specialty_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stage_focus: Mapped[list | None] = mapped_column(JSON, nullable=True)
    contact_channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accepts_remote_case_review: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_verified_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    avg_response_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)


class CasePackage(Base):
    __tablename__ = "case_packages"
    __table_args__ = (UniqueConstraint("case_id", "version_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[dict] = mapped_column(JSON)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OpinionRequest(Base):
    __tablename__ = "opinion_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    status: Mapped[str] = mapped_column(String(30), default="drafted")  # drafted|sent|acknowledged|opinion_received|no_response|declined
    case_package_version_id: Mapped[int | None] = mapped_column(ForeignKey("case_packages.id"), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opinion_recommended_modality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opinion_sequencing_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    opinion_caveats: Mapped[str | None] = mapped_column(Text, nullable=True)
    opinion_requested_tests: Mapped[str | None] = mapped_column(Text, nullable=True)
    conflicts_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor = relationship("Doctor")


class ForeclosureRule(Base):
    __tablename__ = "foreclosure_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    condition_description: Mapped[str] = mapped_column(Text)
    foreclosed_option: Mapped[str] = mapped_column(Text)
    source_guideline: Mapped[str] = mapped_column(String(255))
    source_citation: Mapped[str] = mapped_column(Text)
    cancer_types: Mapped[list | None] = mapped_column(JSON, nullable=True)


class DecisionFlag(Base):
    __tablename__ = "decision_flags"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    foreclosure_rule_id: Mapped[int | None] = mapped_column(ForeignKey("foreclosure_rules.id"), nullable=True)
    flag_type: Mapped[str] = mapped_column(String(30), default="foreclosure")  # foreclosure|coverage_gap
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    rule = relationship("ForeclosureRule")
    case = relationship("Case", back_populates="flags")


class SpecialistCenter(Base):
    __tablename__ = "specialist_centers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cancer_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_verified_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class WaitTimeReport(Base):
    __tablename__ = "wait_time_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    center_name: Mapped[str] = mapped_column(String(255), index=True)
    reported_wait_days: Mapped[int] = mapped_column(Integer)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reported_by_family_id: Mapped[int] = mapped_column(ForeignKey("families.id"))


class TransferRequest(Base):
    __tablename__ = "transfer_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    from_hospital: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_hospital: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="requested")  # requested|received|uploaded
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Trial(Base):
    __tablename__ = "trials"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))  # CTRI|ClinicalTrials.gov
    external_id: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    cancer_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    biomarkers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class CoverageScheme(Base):
    __tablename__ = "coverage_schemes"
    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_name: Mapped[str] = mapped_column(String(255))
    eligibility_criteria_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    covered_treatments: Mapped[list | None] = mapped_column(JSON, nullable=True)
    network_hospitals: Mapped[list | None] = mapped_column(JSON, nullable=True)
    coverage_limit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exclusions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_verified_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class PatientAssistanceProgram(Base):
    __tablename__ = "patient_assistance_programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    drug_name: Mapped[str] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    program_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    eligibility_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_verified_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class CaseFinancialProfile(Base):
    __tablename__ = "case_financial_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), unique=True, index=True)
    insurance_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    insurer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    income_bracket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    budget_ceiling: Mapped[float | None] = mapped_column(Float, nullable=True)
