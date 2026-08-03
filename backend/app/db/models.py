import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class SubscriptionStatus(str, enum.Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    ocr_processing = "ocr_processing"
    extracting = "extracting"
    ready = "ready"
    failed = "failed"


class CaseStatus(str, enum.Enum):
    open = "open"
    needs_documents = "needs_documents"
    ready_for_review = "ready_for_review"
    attorney_reviewed = "attorney_reviewed"
    closed = "closed"


# --------------------------------------------------------------------- #
# Tenancy: every law firm is an Organization. Every user belongs to one.
# --------------------------------------------------------------------- #
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.trialing)

    users = relationship("User", back_populates="organization")
    cases = relationship("Case", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_attorney = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class Client(Base):
    """The immigration firm's own client (the visa applicant)."""
    __tablename__ = "clients"

    id = Column(String, primary_key=True, default=gen_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="client")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=gen_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)

    visa_category = Column(String, nullable=False)  # e.g. "H-1B", "EB-2 NIW", "F-1 OPT"
    status = Column(Enum(CaseStatus), default=CaseStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Populated once the eligibility agent has run
    eligibility_summary = Column(JSON, nullable=True)  # serialized EligibilitySummary schema

    organization = relationship("Organization", back_populates="cases")
    client = relationship("Client", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    flags = relationship("Flag", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)

    document_type = Column(String, nullable=True)  # "passport", "I-797", "employment_letter", etc.
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)

    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploaded)
    ocr_text = Column(Text, nullable=True)
    extracted_fields = Column(JSON, nullable=True)  # structured Pydantic output, serialized
    error_message = Column(Text, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="documents")


class Flag(Base):
    """A discrepancy or missing-proof item raised by the eligibility engine."""
    __tablename__ = "flags"

    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)

    severity = Column(String, nullable=False)  # "blocking" | "warning" | "info"
    category = Column(String, nullable=False)  # "missing_document" | "timeline_conflict" | "eligibility_gap"
    message = Column(Text, nullable=False)
    related_document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    resolved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="flags")
