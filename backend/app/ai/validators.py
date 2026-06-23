"""Validation and safety checks for AI Review Assistant output.

Validation runs before any AI output is saved as a draft finding. It enforces
the output schema, the professional boundary (no prohibited final-decision
language), and source citation integrity. Failures are never hidden: they are
returned with details so the run summary and audit log can record them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import ValidationError

from app.ai.schemas import AIDraftFindingOutput
from app.core.safety import find_prohibited_language


@dataclass
class ValidationOutcome:
    schema_ok: bool = False
    safety_ok: bool = False
    parsed: AIDraftFindingOutput | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.schema_ok and self.safety_ok and not self.errors


def validate_ai_output(
    raw: dict | None, allowed_chunk_ids: set[str]
) -> ValidationOutcome:
    """Validate one raw AI output against the schema and safety rules."""

    outcome = ValidationOutcome()

    if raw is None:
        outcome.errors.append("Provider returned no output.")
        return outcome

    # Schema validation.
    try:
        parsed = AIDraftFindingOutput(**raw)
        outcome.parsed = parsed
        outcome.schema_ok = True
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            outcome.errors.append(f"schema: {loc}: {err.get('msg')}")
        return outcome

    # Non-empty required text fields.
    if not parsed.summary.strip():
        outcome.errors.append("safety: summary is empty.")
    if not parsed.recommended_human_action.strip():
        outcome.errors.append("safety: recommended_human_action is empty.")
    if not parsed.title.strip():
        outcome.errors.append("safety: title is empty.")

    # Source citation integrity.
    if not parsed.source_chunk_ids:
        outcome.errors.append("safety: no source_chunk_ids cited.")
    else:
        invalid = [
            cid for cid in parsed.source_chunk_ids if cid not in allowed_chunk_ids
        ]
        if invalid:
            outcome.errors.append(
                "safety: source_chunk_ids not in retrieved evidence: "
                + ", ".join(invalid)
            )

    # Prohibited final-decision language in any reviewer-facing field.
    for label, text in (
        ("title", parsed.title),
        ("summary", parsed.summary),
        ("recommended_human_action", parsed.recommended_human_action),
        ("finding_type", parsed.finding_type),
    ):
        found = find_prohibited_language(text)
        if found:
            outcome.errors.append(
                f"safety: prohibited wording in {label}: {', '.join(found)}"
            )

    outcome.safety_ok = not any(
        e.startswith("safety:") for e in outcome.errors
    )
    return outcome
