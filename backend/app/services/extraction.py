"""
Step 1 of the agent pipeline: turn a raw uploaded file into structured,
validated fields.

Flow: file bytes -> OCR (Mistral OCR / Gemini vision) -> LLM classification +
field extraction -> ExtractedDocumentFields (validated Pydantic model).
"""
import logging

from app.core.llm_router import LLMRouter
from app.schemas.document import ExtractedDocumentFields

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a meticulous immigration paralegal's assistant.
You will be given the OCR text of a single client document. Classify the document
type and extract every relevant field you can find. Never invent information that
is not present in the text - use null for anything you cannot find. Dates must be
in YYYY-MM-DD format. Set extraction_confidence honestly: lower it if the OCR text
looks garbled or incomplete."""


async def extract_fields_from_document(
    file_bytes: bytes, mime_type: str, provider: str | None = None
) -> tuple[str, ExtractedDocumentFields]:
    """
    Returns (raw_ocr_text, extracted_fields). The raw OCR text is stored too -
    attorneys spot-check against it, and it's what re-extraction retries reuse
    without re-paying for OCR.
    """
    router = LLMRouter(provider=provider)

    ocr_text = await router.ocr_document(file_bytes, mime_type)
    if not ocr_text.strip():
        raise ValueError("OCR returned no text - document may be blank, corrupted, or unsupported format")

    fields = await router.complete_json(
        system=EXTRACTION_SYSTEM_PROMPT,
        user=f"Document OCR text:\n\n{ocr_text}",
        schema=ExtractedDocumentFields,
    )
    return ocr_text, fields
