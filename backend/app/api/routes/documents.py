from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_active_subscription
from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Case, Document, DocumentStatus, User
from app.schemas.document import DocumentDetail, DocumentUploadResponse
from app.services.storage import save_upload
from app.workers.tasks import process_document

router = APIRouter(prefix="/api/cases/{case_id}/documents", tags=["documents"])
settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/tiff", "image/webp",
}


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    case_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(require_active_subscription),
):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.organization_id == user.organization_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {file.content_type}. Allowed: PDF, JPEG, PNG, TIFF, WEBP.",
        )

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit")

    storage_path = save_upload(contents, file.filename)

    doc = Document(
        case_id=case_id,
        original_filename=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type,
        status=DocumentStatus.uploaded,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Hand off to Celery immediately - the HTTP response returns before OCR runs.
    process_document.delay(doc.id)

    return DocumentUploadResponse(id=doc.id, original_filename=doc.original_filename, status=doc.status)


@router.get("", response_model=list[DocumentDetail])
def list_documents(case_id: str, db: Session = Depends(get_db), user: User = Depends(require_active_subscription)):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.organization_id == user.organization_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.documents


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    case_id: str, document_id: str, db: Session = Depends(get_db),
    user: User = Depends(require_active_subscription),
):
    doc = (
        db.query(Document)
        .join(Case)
        .filter(Document.id == document_id, Case.id == case_id, Case.organization_id == user.organization_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
