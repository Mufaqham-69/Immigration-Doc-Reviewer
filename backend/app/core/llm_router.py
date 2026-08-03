"""
Provider-agnostic LLM router.

This is the single most reusable file in the whole skeleton. Every one of the
20 agent concepts calls a different "flavor" of LLM task (fast drafting, vision,
long-context, transcription) from a different free-tier provider. Instead of
hardcoding a provider per concept, every service in this app talks to
`LLMRouter`, and only THIS file knows which vendor SDK is behind it.

To port this skeleton to another concept: change PROVIDER_MODELS below,
everything else in app/services/ stays the same shape.

Usage:
    router = LLMRouter()
    result = await router.complete_json(
        system="You are a visa eligibility analyst.",
        user="<document text>",
        schema=EligibilityFlags,   # a Pydantic model
    )
"""
import json
import logging
from typing import Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)


class LLMError(RuntimeError):
    pass


class LLMRouter:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    async def complete_text(self, system: str, user: str, temperature: float = 0.2) -> str:
        """Free-form text completion."""
        if self.provider == "mistral":
            return await self._mistral_complete(system, user, temperature)
        if self.provider == "gemini":
            return await self._gemini_complete(system, user, temperature)
        raise LLMError(f"Unknown provider: {self.provider}")

    async def complete_json(
        self,
        system: str,
        user: str,
        schema: Type[T],
        temperature: float = 0.0,
        max_retries: int = 2,
    ) -> T:
        """
        Structured extraction. Forces the model to answer with JSON matching
        `schema`, validates it, and retries with the validation error fed
        back to the model if it returns malformed JSON.
        """
        json_instructions = (
            f"\n\nRespond with ONLY valid JSON matching this schema, no prose, "
            f"no markdown fences:\n{schema.model_json_schema()}"
        )
        prompt = user + json_instructions
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            if last_error:
                prompt = (
                    user
                    + json_instructions
                    + f"\n\nYour previous response failed validation with this error, "
                      f"fix it and respond again with ONLY corrected JSON:\n{last_error}"
                )
            raw = await self.complete_text(system, prompt, temperature)
            cleaned = _strip_json_fences(raw)
            try:
                data = json.loads(cleaned)
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = str(exc)
                logger.warning("LLM JSON validation failed (attempt %s): %s", attempt, exc)

        raise LLMError(f"Model failed to produce valid {schema.__name__} after {max_retries + 1} attempts")

    async def ocr_document(self, file_bytes: bytes, mime_type: str) -> str:
        """
        OCR a scanned document (passport, I-797, employment letter, etc).
        Mistral's OCR endpoint and Gemini's native vision both accept base64.
        """
        import base64

        b64 = base64.b64encode(file_bytes).decode()
        if self.provider == "mistral":
            return await self._mistral_ocr(b64, mime_type)
        return await self._gemini_ocr(b64, mime_type)

    # ------------------------------------------------------------------ #
    # Mistral
    # ------------------------------------------------------------------ #
    async def _mistral_complete(self, system: str, user: str, temperature: float) -> str:
        if not settings.MISTRAL_API_KEY:
            raise LLMError("MISTRAL_API_KEY not set")
        headers = {"Authorization": f"Bearer {settings.MISTRAL_API_KEY}"}
        payload = {
            "model": settings.MISTRAL_MODEL,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _mistral_ocr(self, b64: str, mime_type: str) -> str:
        if not settings.MISTRAL_API_KEY:
            raise LLMError("MISTRAL_API_KEY not set")
        headers = {"Authorization": f"Bearer {settings.MISTRAL_API_KEY}"}
        payload = {
            "model": settings.MISTRAL_OCR_MODEL,
            "document": {"type": "document_url", "document_url": f"data:{mime_type};base64,{b64}"},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.mistral.ai/v1/ocr", headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("pages", [])
            return "\n\n".join(p.get("markdown", "") for p in pages)

    # ------------------------------------------------------------------ #
    # Gemini
    # ------------------------------------------------------------------ #
    async def _gemini_complete(self, system: str, user: str, temperature: float) -> str:
        if not settings.GOOGLE_API_KEY:
            raise LLMError("GOOGLE_API_KEY not set")
        url = GEMINI_API_URL_TEMPLATE.format(model=settings.GEMINI_MODEL, key=settings.GOOGLE_API_KEY)
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _gemini_ocr(self, b64: str, mime_type: str) -> str:
        if not settings.GOOGLE_API_KEY:
            raise LLMError("GOOGLE_API_KEY not set")
        url = GEMINI_API_URL_TEMPLATE.format(model=settings.GEMINI_MODEL, key=settings.GOOGLE_API_KEY)
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": "Transcribe this document to plain text/markdown. Preserve all dates, "
                                  "names, and reference numbers exactly as written."},
                        {"inline_data": {"mime_type": mime_type, "data": b64}},
                    ],
                }
            ]
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.replace("```json", "").replace("```", "")
    return text.strip()
