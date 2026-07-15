"""Reference-candidate building, basin-conflict detection, and layer findings.

Runs after DXF text and layer extraction. Builds reference candidates from
extracted text, matches sheet and detail references against seeded plan sheets,
detects possible facility naming inconsistencies, and raises review-support
findings for unknown layer categories. Every result needs human review and is
never a confirmed design conflict or a final engineering decision.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import models
from app.services.cad import facility_identity, layer_taxonomy, reference_parser
from app.services.cad_intake_service._common import _create_finding, _short

# Layer classification is delegated to the data-driven taxonomy in
# app.services.cad.layer_taxonomy. NEUTRAL_LAYERS is re-exported for callers
# that referenced it here.
NEUTRAL_LAYERS = layer_taxonomy.NEUTRAL_LAYERS


def _build_reference_candidates(
    db: Session,
    run: models.CadParseRun,
    text_extracts: list[models.CadTextExtract],
    sheet_map: dict[str, str],
) -> None:
    basin_labels: list[tuple[str, models.CadTextExtract]] = []

    for text in text_extracts:
        normalized = text.normalized_text
        parsed = reference_parser.parse_references(normalized)

        for reference in parsed:
            if reference.reference_type == "detail_reference":
                sheet_token = reference.sheet_token
                matched_id = sheet_map.get(sheet_token)
                if reference.ambiguous:
                    confidence = "needs_human_review"
                    reason = (
                        reference.ambiguity_reason
                        or "Detail or sheet token is ambiguous and needs "
                        "human review."
                    )
                elif matched_id:
                    confidence = "high"
                    reason = (
                        f"Detail sheet {sheet_token} matches a seeded plan "
                        "sheet."
                    )
                else:
                    confidence = "low"
                    reason = (
                        f"Detail sheet {sheet_token} has no matching seeded "
                        "plan sheet."
                    )
                candidate = _add_candidate(
                    db,
                    run=run,
                    reference_text=reference.normalized_reference,
                    normalized_reference=sheet_token,
                    reference_type="detail_reference",
                    source_text=text,
                    matched_plan_sheet_id=None if reference.ambiguous else matched_id,
                    confidence_label=confidence,
                    match_reason=reason,
                )
                if reference.ambiguous:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="unclear_detail_reference",
                        title=(
                            "Unclear detail reference: "
                            f"{reference.normalized_reference}"
                        ),
                        description=(
                            "The detail reference could not be resolved and "
                            "needs human review."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )
                elif not matched_id:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=f"Detail references missing sheet {sheet_token}",
                        description=(
                            f"Sheet {sheet_token} referenced by a detail "
                            "callout has no matching seeded plan sheet."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )
            else:
                sheet_token = reference.sheet_token
                matched_id = (
                    None if reference.ambiguous else sheet_map.get(sheet_token)
                )
                if reference.ambiguous:
                    confidence = "needs_human_review"
                    reason = (
                        reference.ambiguity_reason
                        or f"Sheet {sheet_token} is ambiguous."
                    )
                elif matched_id:
                    confidence = "high"
                    reason = f"Sheet {sheet_token} matches seeded plan sheet."
                else:
                    confidence = "needs_human_review"
                    reason = (
                        f"Sheet {sheet_token} has no matching seeded plan "
                        "sheet."
                    )
                candidate = _add_candidate(
                    db,
                    run=run,
                    reference_text=reference.raw_text,
                    normalized_reference=sheet_token,
                    reference_type="sheet_reference",
                    source_text=text,
                    matched_plan_sheet_id=matched_id,
                    confidence_label=confidence,
                    match_reason=reason,
                )
                if not matched_id and not reference.ambiguous:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=(
                            f"Referenced sheet {sheet_token} has no plan "
                            "sheet match"
                        ),
                        description=(
                            f"The DXF references sheet {sheet_token}, which "
                            "has no matching seeded plan sheet. Reviewer "
                            "confirmation needed."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )

        if parsed:
            continue

        if text.reference_type == "basin_label":
            candidate = _add_candidate(
                db,
                run=run,
                reference_text=text.text_value,
                normalized_reference=normalized,
                reference_type="basin_label",
                source_text=text,
                matched_plan_sheet_id=None,
                confidence_label="medium",
                match_reason="Basin label extracted for reviewer confirmation.",
            )
            basin_labels.append((normalized, text))
        elif text.reference_type in {
            "pipe_label",
            "outfall_label",
            "wetland_buffer_label",
            "revision_note",
        }:
            _add_candidate(
                db,
                run=run,
                reference_text=text.text_value,
                normalized_reference=normalized,
                reference_type=text.reference_type,
                source_text=text,
                matched_plan_sheet_id=None,
                confidence_label="medium",
                match_reason=f"{text.reference_type.replace('_', ' ')} extracted "
                "for reviewer confirmation.",
            )

    _detect_basin_conflicts(db, run, basin_labels)


def _add_candidate(
    db: Session,
    *,
    run: models.CadParseRun,
    reference_text: str,
    normalized_reference: str,
    reference_type: str,
    source_text: models.CadTextExtract,
    matched_plan_sheet_id: str | None,
    confidence_label: str,
    match_reason: str,
) -> models.CadReferenceCandidate:
    candidate = models.CadReferenceCandidate(
        candidate_id=f"cadref_{_short()}",
        parse_run_id=run.parse_run_id,
        cad_file_id=run.cad_file_id,
        project_id=run.project_id,
        reference_text=reference_text,
        normalized_reference=normalized_reference,
        reference_type=reference_type,
        source_entity_id=None,
        source_text_id=source_text.text_extract_id,
        matched_plan_sheet_id=matched_plan_sheet_id,
        matched_plan_reference_id=None,
        confidence_label=confidence_label,
        match_reason=match_reason,
        requires_human_review=confidence_label in {"low", "needs_human_review"},
    )
    db.add(candidate)
    return candidate


def _detect_basin_conflicts(
    db: Session,
    run: models.CadParseRun,
    basin_labels: list[tuple[str, models.CadTextExtract]],
) -> None:
    """Raise possible naming inconsistencies between facility labels.

    Uses structured facility identities so different facility types that share
    a number (DETENTION BASIN 1 and INFILTRATION BASIN 1) are never flagged as
    the same facility. Each finding names both labels, the rule, and why the
    labels may refer to the same facility. These are possible naming
    inconsistencies that need reviewer confirmation, never confirmed design
    conflicts.
    """

    identities: list[facility_identity.FacilityIdentity] = []
    source_by_label: dict[str, models.CadTextExtract] = {}
    for normalized, text in basin_labels:
        location = None
        if text.x is not None and text.y is not None:
            location = (text.x, text.y)
        identity = facility_identity.parse_facility_label(
            normalized, location=location
        )
        if identity is None:
            continue
        identities.append(identity)
        source_by_label.setdefault(identity.normalized_label, text)

    for conflict in facility_identity.detect_facility_conflicts(identities):
        joined = ", ".join(conflict.labels)
        sample_text = source_by_label.get(conflict.labels[0])
        _create_finding(
            db,
            run=run,
            finding_type="possible_label_conflict",
            title=(
                "Possible facility naming inconsistency for "
                f"'{conflict.identifier or joined}'"
            ),
            description=(
                f"Labels: {joined}. {conflict.reason} Matching rule: "
                f"{conflict.rule}. Confidence: {conflict.confidence}."
            ),
            severity="medium",
            source_text_extract_id=(
                sample_text.text_extract_id if sample_text else None
            ),
        )


def _build_layer_findings(
    db: Session, run: models.CadParseRun, layers: list[models.CadLayerExtract]
) -> None:
    for layer in layers:
        if layer.review_category != "unknown":
            continue
        if layer.entity_count == 0:
            continue
        if layer.layer_name.upper() in NEUTRAL_LAYERS:
            continue
        _create_finding(
            db,
            run=run,
            finding_type="unknown_layer_category",
            title=f"Layer '{layer.layer_name}' could not be categorized",
            description=(
                f"Layer '{layer.layer_name}' has {layer.entity_count} entities "
                "but no recognized review category. Reviewer categorization "
                "needed."
            ),
            severity="low",
            source_layer_extract_id=layer.layer_extract_id,
        )
