"""
Visa category rule packs.

This is the part of the product that actually needs ongoing maintenance —
USCIS/consular requirements change. Treat this file (or, once you outgrow it,
a proper admin-editable table) as your firm's living knowledge base rather
than something you write once. Each firm using the product may also want to
add their own internal checklist items on top of the baseline federal ones.

Keep this data-only (no logic) so non-engineers on your team can eventually
edit it without touching Python.
"""

VISA_RULES: dict[str, dict] = {
    "H-1B": {
        "required_document_types": [
            "passport", "i797_notice", "employment_letter", "degree_certificate",
        ],
        "timeline_checks": [
            "Degree conferral date must precede employment start date",
            "I-797 validity period must cover the intended employment period",
        ],
        "notes": "Specialty occupation - degree relevance to job duties is the most common RFE trigger.",
    },
    "EB-2 NIW": {
        "required_document_types": [
            "passport", "degree_certificate", "employment_letter",
        ],
        "timeline_checks": [
            "Advanced degree or exceptional ability evidence must predate petition filing",
        ],
        "notes": "National interest waiver - petition strength depends heavily on supporting evidence "
                 "not captured by document OCR (recommendation letters, publications). Flag for attorney "
                 "narrative review rather than automated pass/fail.",
    },
    "F-1 OPT": {
        "required_document_types": [
            "passport", "i797_notice", "degree_certificate",
        ],
        "timeline_checks": [
            "OPT application window is within 90 days before to 60 days after program end date",
        ],
        "notes": "STEM OPT extensions require an additional employer attestation document type "
                 "not modeled here yet - extend required_document_types when you add that flow.",
    },
    "L-1A": {
        "required_document_types": [
            "passport", "employment_letter",
        ],
        "timeline_checks": [
            "Applicant must show 1 continuous year of qualifying employment abroad within the "
            "past 3 years before the petition",
        ],
        "notes": "Intracompany transferee - foreign entity relationship documentation is required "
                 "but usually submitted as a single combined PDF; consider a dedicated document_type "
                 "for it if volume grows.",
    },
}


def get_rule_pack(visa_category: str) -> dict:
    pack = VISA_RULES.get(visa_category)
    if not pack:
        # Graceful fallback so unknown/custom categories don't crash the pipeline -
        # they just skip automated checklist matching and rely on the LLM's general
        # knowledge plus attorney review.
        return {
            "required_document_types": [],
            "timeline_checks": [],
            "notes": f"No rule pack configured for '{visa_category}' yet - add one to "
                     f"app/visa_rules/rules.py for automated checklist matching.",
        }
    return pack
