"""
Step 2 of the agent pipeline: once every document in a case has been
extracted, cross-reference the whole set against the visa category's rule
pack, catch timeline conflicts, and produce the attorney-facing summary.

Deterministic checks (missing document types, simple date-ordering) are done
in plain Python - cheap, fast, and don't hallucinate. The LLM is used only
for the parts that need judgment: writing the timeline narrative and
synthesizing the attorney briefing. This split (rules engine + LLM synthesis,
not LLM-does-everything) is what keeps this reliable enough for a law firm
to trust.
"""
import logging

from app.core.llm_router import LLMRouter
from app.schemas.case import EligibilityFlag, EligibilitySummary
from app.schemas.document import ExtractedDocumentFields
from app.visa_rules.rules import get_rule_pack

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """You are drafting a case triage briefing for a licensed immigration
attorney. You are given: the visa category, a rule pack of requirements, structured data
extracted from every document in the case, and a list of flags already identified by
deterministic checks. Write a chronological timeline_narrative from the extracted key_dates
and issue/expiry dates across all documents. Write attorney_notes as a tight 2-4 sentence
briefing - what looks solid, what needs the attorney's judgment call, nothing a rules engine
already caught verbatim. Never provide a legal conclusion about whether the case will be
approved - that is the attorney's call, not yours."""


def _run_deterministic_checks(
    visa_category: str, documents: list[ExtractedDocumentFields]
) -> tuple[list[EligibilityFlag], list[str]]:
    rule_pack = get_rule_pack(visa_category)
    flags: list[EligibilityFlag] = []

    present_types = {d.document_type for d in documents}
    required_types = set(rule_pack["required_document_types"])
    missing_types = sorted(required_types - present_types)

    for missing in missing_types:
        flags.append(
            EligibilityFlag(
                severity="blocking",
                category="missing_document",
                message=f"No {missing.replace('_', ' ')} has been uploaded yet, and this is "
                        f"required for {visa_category}.",
                related_document_type=missing,
            )
        )

    # Low-confidence extractions are worth a human glance before they're trusted.
    for doc in documents:
        if doc.extraction_confidence < 0.6:
            flags.append(
                EligibilityFlag(
                    severity="warning",
                    category="data_inconsistency",
                    message=f"Extraction confidence for the {doc.document_type.replace('_', ' ')} "
                            f"was low ({doc.extraction_confidence:.0%}) - worth a manual check "
                            f"against the original scan.",
                    related_document_type=doc.document_type,
                )
            )

    # Simple, generic timeline sanity check: expired documents.
    for doc in documents:
        if doc.expiry_date and doc.document_number:
            from datetime import date
            if doc.expiry_date < date.today():
                flags.append(
                    EligibilityFlag(
                        severity="blocking",
                        category="timeline_conflict",
                        message=f"The {doc.document_type.replace('_', ' ')} "
                                f"(doc #{doc.document_number}) expired on {doc.expiry_date.isoformat()}.",
                        related_document_type=doc.document_type,
                    )
                )

    return flags, missing_types


async def build_case_summary(
    visa_category: str,
    documents: list[ExtractedDocumentFields],
    provider: str | None = None,
) -> EligibilitySummary:
    deterministic_flags, missing_types = _run_deterministic_checks(visa_category, documents)
    rule_pack = get_rule_pack(visa_category)

    router = LLMRouter(provider=provider)
    synthesis_input = {
        "visa_category": visa_category,
        "rule_pack": rule_pack,
        "documents": [d.model_dump(mode="json") for d in documents],
        "deterministic_flags_already_found": [f.model_dump() for f in deterministic_flags],
    }

    class _Narrative(EligibilitySummary):
        # Reuse the same schema for the synthesis call; the LLM only needs to
        # fill timeline_narrative + attorney_notes + overall_readiness sensibly,
        # everything else we already computed and will overwrite below.
        pass

    llm_summary = await router.complete_json(
        system=SYNTHESIS_SYSTEM_PROMPT,
        user=f"Case data:\n\n{synthesis_input}",
        schema=_Narrative,
    )

    blocking_count = sum(1 for f in deterministic_flags if f.severity == "blocking")
    if blocking_count > 0:
        readiness = "not_ready"
    elif any(f.severity == "warning" for f in deterministic_flags):
        readiness = "needs_attention"
    else:
        readiness = "ready_to_file"

    return EligibilitySummary(
        visa_category=visa_category,
        documents_reviewed=len(documents),
        overall_readiness=readiness,  # deterministic, not LLM-decided
        flags=deterministic_flags,  # deterministic, not LLM-decided
        timeline_narrative=llm_summary.timeline_narrative,
        missing_document_types=missing_types,
        attorney_notes=llm_summary.attorney_notes,
    )
