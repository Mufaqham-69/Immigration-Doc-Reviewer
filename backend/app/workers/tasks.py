"""
Async jobs. Kept as thin wrappers around app/services/* so the actual agent
logic stays testable without spinning up Celery/Redis.
"""
import asyncio
import logging
from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import Case, CaseStatus, Document, DocumentStatus
from app.schemas.document import ExtractedDocumentFields
from app.services.eligibility_engine import build_case_summary
from app.services.extraction import extract_fields_from_document
from app.services.storage import read_file
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Celery workers are sync; the LLM router is async (httpx). Bridge the two."""
    return asyncio.run(coro)


@celery_app.task(name="process_document", bind=True, max_retries=2)
def process_document(self, document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("process_document: document %s not found", document_id)
            return

        doc.status = DocumentStatus.ocr_processing
        db.commit()

        file_bytes = read_file(doc.storage_path)

        doc.status = DocumentStatus.extracting
        db.commit()

        ocr_text, fields = _run_async(extract_fields_from_document(file_bytes, doc.mime_type))

        doc.ocr_text = ocr_text
        doc.document_type = fields.document_type
        doc.extracted_fields = fields.model_dump(mode="json")
        doc.status = DocumentStatus.ready
        doc.processed_at = datetime.utcnow()
        db.commit()

        # Once a document lands, refresh the whole case's eligibility summary
        # so the attorney's view is always current.
        recompute_case_eligibility.delay(doc.case_id)

    except Exception as exc:  # noqa: BLE001
        logger.exception("process_document failed for %s", document_id)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.failed
            doc.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="recompute_case_eligibility")
def recompute_case_eligibility(case_id: str):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return

        ready_docs = (
            db.query(Document)
            .filter(Document.case_id == case_id, Document.status == DocumentStatus.ready)
            .all()
        )
        if not ready_docs:
            return

        extracted = [
            ExtractedDocumentFields.model_validate(d.extracted_fields) for d in ready_docs
        ]
        summary = _run_async(build_case_summary(case.visa_category, extracted))

        case.eligibility_summary = summary.model_dump(mode="json")
        case.status = (
            CaseStatus.ready_for_review
            if summary.overall_readiness != "not_ready"
            else CaseStatus.needs_documents
        )
        db.commit()
    except Exception:
        logger.exception("recompute_case_eligibility failed for case %s", case_id)
        raise
    finally:
        db.close()
