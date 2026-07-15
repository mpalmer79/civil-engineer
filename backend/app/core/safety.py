"""Canonical safety guardrail language for Civil Engineer AI.

Civil Engineer AI is a review-support and evidence-organization system. It must
never present itself as a licensed engineering tool. This module is the single
source of truth for the final-decision language the system must never apply to
a status or finding conclusion, the sanctioned review-support phrasing, and the
helper functions that enforce the boundary.

Layout: the guardrail language and enforcement helpers live here. The
per-domain status and action vocabularies (allowed statuses, action types, and
transition maps for each bounded context) live in the app.core.vocab package.
This module re-exports every vocabulary name from app.core.vocab so existing
imports of the form "from app.core.safety import X" and attribute access via
"safety.X" keep working unchanged.

Explanatory prose elsewhere may state that the system does not approve plans.
That is different from applying a prohibited word as a status or conclusion,
which this module exists to prevent.
"""

from __future__ import annotations

# Re-export the per-domain status and action vocabularies. app.core.vocab
# defines __all__, so this binds every vocabulary name in this module and
# preserves the stable import surface of app.core.safety.
from app.core.vocab import *  # noqa: F401,F403

# Final-decision language the system must never use as a status or conclusion.
# Matching is done case insensitively against normalized text.
PROHIBITED_FINAL_DECISION_WORDS: set[str] = {
    "approved",
    "certified",
    "fully compliant",
    "safe",
    "engineer-confirmed",
    "passes review",
    "meets all requirements",
}

# Standard note attached to retrieval and evidence responses to keep the
# professional boundary explicit in API payloads and the UI.
EVIDENCE_SAFETY_NOTE: str = (
    "This is source evidence for reviewer evaluation, not a final engineering "
    "conclusion."
)

# Sanctioned review-support phrasing, kept here for reference and reuse.
SANCTIONED_REVIEW_LANGUAGE: set[str] = {
    "potential issue",
    "requires reviewer confirmation",
    "missing evidence",
    "conflicting information",
    "based on submitted documents",
    "recommended follow-up",
    "needs human review",
    "review-support finding",
}


class ProhibitedLanguageError(ValueError):
    """Raised when user-provided text contains final-decision wording."""


def reject_prohibited_language(text: str | None, *, field: str) -> None:
    """Raise ProhibitedLanguageError if text uses final-decision wording.

    Used to keep reviewer-provided titles, categories, and notes within the
    review-support boundary. Long explanatory prose is not the target here; the
    short, labelled fields of a project, document, or finding are.
    """

    found = find_prohibited_language(text)
    if found:
        raise ProhibitedLanguageError(
            f"The {field} contains prohibited final-decision wording: "
            f"{', '.join(sorted(found))}. Use review-support language."
        )


def is_allowed_status(status: str) -> bool:
    """Return True if the status is in the allowed review vocabulary."""

    return status in ALLOWED_REVIEW_STATUSES


def is_human_review_status(status: str) -> bool:
    """Return True if the status keeps the finding under human review."""

    return status in HUMAN_REVIEW_STATUSES


def contains_prohibited_language(text: str | None) -> bool:
    """Return True if text contains any prohibited final-decision wording.

    This is intended for validating statuses and short conclusion labels, not
    for scanning long explanatory prose that may legitimately discuss what the
    system does not do.
    """

    if not text:
        return False
    normalized = text.strip().lower()
    return any(word in normalized for word in PROHIBITED_FINAL_DECISION_WORDS)


def find_prohibited_language(text: str | None) -> list[str]:
    """Return the list of prohibited words found in text, if any."""

    if not text:
        return []
    normalized = text.strip().lower()
    return [word for word in PROHIBITED_FINAL_DECISION_WORDS if word in normalized]
