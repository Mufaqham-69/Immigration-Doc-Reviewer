from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedDocumentFields(BaseModel):
    """
    What the extraction agent pulls out of ANY client document. Kept generic
    (not "passport-only" or "I-797-only") because a law firm's inbox mixes
    document types and we classify + extract in one LLM call.
    """
    document_type: Literal[
        "passport", "visa_stamp", "i797_notice", "employment_letter",
        "degree_certificate", "pay_stub", "tax_return", "marriage_certificate",
        "birth_certificate", "lease_agreement", "bank_statement", "other",
    ] = Field(description="Best-guess classification of the document")

    full_name: str | None = Field(default=None, description="Name as printed on the document")
    document_number: str | None = Field(default=None, description="Passport #, receipt #, etc.")
    issue_date: date | None = None
    expiry_date: date | None = None
    issuing_authority: str | None = None

    key_dates: list[str] = Field(
        default_factory=list,
        description="Any other dates on the document relevant to a timeline, as ISO strings",
    )
    employer_name: str | None = None
    job_title: str | None = None
    annual_salary_usd: float | None = None

    raw_notes: str = Field(
        default="", description="Anything notable the classifier fields above don't capture"
    )
    extraction_confidence: float = Field(
        ge=0.0, le=1.0, description="Model's own confidence in this extraction, 0-1"
    )


class DocumentUploadResponse(BaseModel):
    id: str
    original_filename: str
    status: str


class DocumentDetail(BaseModel):
    id: str
    case_id: str
    document_type: str | None
    original_filename: str
    status: str
    extracted_fields: ExtractedDocumentFields | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True
