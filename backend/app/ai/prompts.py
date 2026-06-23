"""Prompt construction for the AI Review Assistant.

Prompts are constrained: the model reviews one checklist item using only the
retrieved source evidence, must cite chunk ids, must not use outside knowledge,
and must not make final engineering decisions.
"""

from __future__ import annotations

import json

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

PROMPT_VERSION = "checklist_review_v1"


def _format_evidence(evidence: list[dict]) -> str:
    lines = []
    for item in evidence:
        lines.append(
            json.dumps(
                {
                    "chunk_id": item.get("chunk_id"),
                    "document": item.get("file_name"),
                    "page": item.get("page_number"),
                    "section": item.get("section_heading"),
                    "excerpt": item.get("excerpt"),
                }
            )
        )
    return "\n".join(lines) if lines else "No source evidence was retrieved."


def build_checklist_review_prompt(
    checklist_item: dict, evidence: list[dict]
) -> str:
    """Build a constrained review prompt for one checklist item."""

    prohibited = ", ".join(sorted(PROHIBITED_FINAL_DECISION_WORDS))
    checklist_block = json.dumps(
        {
            "checklist_item_id": checklist_item.get("checklist_item_id"),
            "category": checklist_item.get("category"),
            "requirement": checklist_item.get("requirement"),
            "expected_evidence": checklist_item.get("expected_evidence"),
        },
        indent=2,
    )

    return f"""You are assisting a human stormwater reviewer. You are not approving plans or certifying compliance.

Task:
Review the checklist item using only the provided source evidence.

Checklist item:
{checklist_block}

Source evidence:
{_format_evidence(evidence)}

Rules:
- Use only the provided source evidence.
- Do not use outside knowledge.
- Do not approve the project.
- Do not certify compliance.
- Do not declare the design safe.
- Do not use any of these words as a status or conclusion: {prohibited}.
- If evidence is missing, unclear, or conflicting, say so.
- Every finding must require human reviewer confirmation.
- Cite source chunk ids for every evidence-based statement.
- Return only valid JSON matching the required schema, with keys:
  checklist_item_id, finding_type, title, summary, risk_level, confidence,
  source_chunk_ids, recommended_human_action, requires_human_review,
  safety_boundary_acknowledged.
- requires_human_review must be true and safety_boundary_acknowledged must be true.
"""
