"""Data-driven civil CAD layer taxonomy.

Classifies DXF layer names into descriptive review-support categories. The
taxonomy is a typed, ordered rule table: exact aliases first, then token rules,
then prefix rules. First match wins within a priority band. A category is a
routing aid for the reviewer, never a conclusion: a layer named C-STORM is
routed to the stormwater queue, but nothing here checks that the layer content
is correct, complete, or compliant.

Unknown is an explicit, reviewable state, not an error. Layers that cannot be
classified keep their entity inventory and receive a low-severity
review-support observation so a reviewer can categorize them.

Naming caveat recorded here on purpose: the PROP token is used by some firms
for property lines and by others as a proposed-work modifier. This taxonomy
maps a bare PROP token to property_boundary at medium confidence and lets more
specific compound tokens (for example C-PROP-ROAD, C-PROP-GRAD) route to their
subject category first. A reviewer mapping can override any assignment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Review categories. The first eight existed before this module and are kept
# stable because persisted rows and the frontend already use them. The rest
# were added when the taxonomy became data driven.
CATEGORY_PROPERTY_BOUNDARY = "property_boundary"
CATEGORY_ROAD_ALIGNMENT = "road_alignment"
CATEGORY_LOTS_PARCELS = "lots_parcels"
CATEGORY_GRADING = "grading"
CATEGORY_STORMWATER = "stormwater"
CATEGORY_WETLAND = "wetland_buffer"
CATEGORY_EROSION = "erosion_control"
CATEGORY_UTILITIES = "utilities"
CATEGORY_ANNOTATION = "annotation"
CATEGORY_NOTES = "notes"
CATEGORY_TITLEBLOCK = "titleblock"
CATEGORY_LANDSCAPE = "landscape"
CATEGORY_EXISTING = "existing_conditions"
CATEGORY_SURVEY_CONTROL = "survey_control"
CATEGORY_STRUCTURES = "structures"
CATEGORY_UNKNOWN = "unknown"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

# Layers that carry no review meaning on their own.
NEUTRAL_LAYERS: set[str] = {"0", "DEFPOINTS"}


@dataclass(frozen=True)
class LayerRule:
    """One taxonomy rule. kind is exact, token, or prefix."""

    kind: str
    pattern: str
    category: str
    confidence: str
    explanation: str


@dataclass(frozen=True)
class LayerClassification:
    """The classification result for one layer name."""

    layer_name: str
    normalized_name: str
    category: str
    confidence: str
    rule_kind: str
    rule_pattern: str
    explanation: str
    unknown_reason: str | None = None
    tokens: tuple[str, ...] = field(default_factory=tuple)

    @property
    def requires_human_review(self) -> bool:
        return self.category == CATEGORY_UNKNOWN


def _rule(
    kind: str, pattern: str, category: str, confidence: str, explanation: str
) -> LayerRule:
    return LayerRule(kind, pattern, category, confidence, explanation)


# Ordered rule table. Earlier rules win. Subject tokens (road, grading, storm)
# come before the PROP and EXST modifiers so C-PROP-ROAD routes to
# road_alignment and C-EXST-UTIL routes to utilities rather than to the
# modifier category.
LAYER_RULES: list[LayerRule] = [
    # Exact aliases for the most common civil layer names.
    _rule("exact", "C-PROP", CATEGORY_PROPERTY_BOUNDARY, CONFIDENCE_MEDIUM,
          "C-PROP commonly holds property lines. Some firms use PROP for "
          "proposed work, so a reviewer can override this."),
    _rule("exact", "C-ROAD", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_HIGH,
          "C-ROAD holds road geometry and alignments."),
    _rule("exact", "C-LOTS", CATEGORY_LOTS_PARCELS, CONFIDENCE_HIGH,
          "C-LOTS holds lot and parcel linework."),
    _rule("exact", "C-LABEL", CATEGORY_ANNOTATION, CONFIDENCE_HIGH,
          "C-LABEL holds annotation labels."),
    _rule("exact", "C-LANDSCAPE", CATEGORY_LANDSCAPE, CONFIDENCE_HIGH,
          "C-LANDSCAPE holds landscape planting content."),
    # Subject tokens.
    _rule("token", "ROAD", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_HIGH,
          "ROAD token indicates road or alignment content."),
    _rule("token", "ALIGN", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_MEDIUM,
          "ALIGN token indicates alignment geometry."),
    _rule("token", "CURB", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_MEDIUM,
          "CURB token indicates roadway curbing."),
    _rule("token", "PVMT", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_MEDIUM,
          "PVMT token indicates pavement."),
    _rule("token", "STREET", CATEGORY_ROAD_ALIGNMENT, CONFIDENCE_MEDIUM,
          "STREET token indicates roadway content."),
    _rule("token", "LOT", CATEGORY_LOTS_PARCELS, CONFIDENCE_HIGH,
          "LOT token indicates lot linework."),
    _rule("token", "LOTS", CATEGORY_LOTS_PARCELS, CONFIDENCE_HIGH,
          "LOTS token indicates lot linework."),
    _rule("token", "PARCEL", CATEGORY_LOTS_PARCELS, CONFIDENCE_HIGH,
          "PARCEL token indicates parcel linework."),
    _rule("token", "GRAD", CATEGORY_GRADING, CONFIDENCE_HIGH,
          "GRAD token indicates grading content."),
    _rule("token", "CONT", CATEGORY_GRADING, CONFIDENCE_MEDIUM,
          "CONT token indicates contour linework."),
    _rule("token", "CONTOUR", CATEGORY_GRADING, CONFIDENCE_HIGH,
          "CONTOUR token indicates contour linework."),
    _rule("token", "TOPO", CATEGORY_GRADING, CONFIDENCE_MEDIUM,
          "TOPO token indicates topographic content."),
    _rule("token", "STORM", CATEGORY_STORMWATER, CONFIDENCE_HIGH,
          "STORM token indicates storm drainage."),
    _rule("token", "STRM", CATEGORY_STORMWATER, CONFIDENCE_HIGH,
          "STRM token indicates storm drainage."),
    _rule("token", "DRAN", CATEGORY_STORMWATER, CONFIDENCE_MEDIUM,
          "DRAN token indicates drainage."),
    _rule("token", "DRAIN", CATEGORY_STORMWATER, CONFIDENCE_HIGH,
          "DRAIN token indicates drainage."),
    _rule("token", "SDRAIN", CATEGORY_STORMWATER, CONFIDENCE_MEDIUM,
          "SDRAIN token indicates storm drainage."),
    _rule("token", "WETL", CATEGORY_WETLAND, CONFIDENCE_HIGH,
          "WETL token indicates wetland content."),
    _rule("token", "WETLAND", CATEGORY_WETLAND, CONFIDENCE_HIGH,
          "WETLAND token indicates wetland content."),
    _rule("token", "WTLND", CATEGORY_WETLAND, CONFIDENCE_HIGH,
          "WTLND token indicates wetland content."),
    _rule("token", "BUFFER", CATEGORY_WETLAND, CONFIDENCE_MEDIUM,
          "BUFFER token indicates a resource buffer."),
    _rule("token", "EROS", CATEGORY_EROSION, CONFIDENCE_HIGH,
          "EROS token indicates erosion and sediment control."),
    _rule("token", "ESC", CATEGORY_EROSION, CONFIDENCE_MEDIUM,
          "ESC token indicates erosion and sediment control."),
    _rule("token", "SILT", CATEGORY_EROSION, CONFIDENCE_MEDIUM,
          "SILT token indicates sediment control."),
    _rule("token", "UTIL", CATEGORY_UTILITIES, CONFIDENCE_HIGH,
          "UTIL token indicates utilities."),
    _rule("token", "WATR", CATEGORY_UTILITIES, CONFIDENCE_MEDIUM,
          "WATR token indicates water utilities."),
    _rule("token", "SSWR", CATEGORY_UTILITIES, CONFIDENCE_MEDIUM,
          "SSWR token indicates sanitary sewer."),
    _rule("token", "SAN", CATEGORY_UTILITIES, CONFIDENCE_MEDIUM,
          "SAN token indicates sanitary sewer."),
    _rule("token", "ELEC", CATEGORY_UTILITIES, CONFIDENCE_MEDIUM,
          "ELEC token indicates electric utilities."),
    _rule("token", "GAS", CATEGORY_UTILITIES, CONFIDENCE_MEDIUM,
          "GAS token indicates gas utilities."),
    _rule("token", "LABEL", CATEGORY_ANNOTATION, CONFIDENCE_HIGH,
          "LABEL token indicates annotation labels."),
    _rule("token", "ANNO", CATEGORY_ANNOTATION, CONFIDENCE_HIGH,
          "ANNO token indicates annotation."),
    _rule("token", "TEXT", CATEGORY_ANNOTATION, CONFIDENCE_MEDIUM,
          "TEXT token indicates annotation text."),
    _rule("token", "DIMS", CATEGORY_ANNOTATION, CONFIDENCE_MEDIUM,
          "DIMS token indicates dimension annotation."),
    _rule("token", "NOTE", CATEGORY_NOTES, CONFIDENCE_HIGH,
          "NOTE token indicates plan notes."),
    _rule("token", "NOTES", CATEGORY_NOTES, CONFIDENCE_HIGH,
          "NOTES token indicates plan notes."),
    _rule("token", "TITLE", CATEGORY_TITLEBLOCK, CONFIDENCE_HIGH,
          "TITLE token indicates titleblock content."),
    _rule("token", "TTLB", CATEGORY_TITLEBLOCK, CONFIDENCE_MEDIUM,
          "TTLB token indicates titleblock content."),
    _rule("token", "LANDSCAPE", CATEGORY_LANDSCAPE, CONFIDENCE_HIGH,
          "LANDSCAPE token indicates landscape content."),
    _rule("token", "LSCP", CATEGORY_LANDSCAPE, CONFIDENCE_MEDIUM,
          "LSCP token indicates landscape content."),
    _rule("token", "PLNT", CATEGORY_LANDSCAPE, CONFIDENCE_MEDIUM,
          "PLNT token indicates planting."),
    _rule("token", "TREE", CATEGORY_LANDSCAPE, CONFIDENCE_MEDIUM,
          "TREE token indicates planting."),
    _rule("token", "SURV", CATEGORY_SURVEY_CONTROL, CONFIDENCE_MEDIUM,
          "SURV token indicates survey content."),
    _rule("token", "CTRL", CATEGORY_SURVEY_CONTROL, CONFIDENCE_MEDIUM,
          "CTRL token indicates survey control."),
    _rule("token", "MONU", CATEGORY_SURVEY_CONTROL, CONFIDENCE_MEDIUM,
          "MONU token indicates survey monuments."),
    _rule("token", "BLDG", CATEGORY_STRUCTURES, CONFIDENCE_HIGH,
          "BLDG token indicates building structures."),
    _rule("token", "STRC", CATEGORY_STRUCTURES, CONFIDENCE_MEDIUM,
          "STRC token indicates structures."),
    _rule("token", "WALL", CATEGORY_STRUCTURES, CONFIDENCE_MEDIUM,
          "WALL token indicates wall structures."),
    # Modifier tokens after the subject tokens.
    _rule("token", "BOUND", CATEGORY_PROPERTY_BOUNDARY, CONFIDENCE_HIGH,
          "BOUND token indicates boundary linework."),
    _rule("token", "BNDY", CATEGORY_PROPERTY_BOUNDARY, CONFIDENCE_MEDIUM,
          "BNDY token indicates boundary linework."),
    _rule("token", "ROW", CATEGORY_PROPERTY_BOUNDARY, CONFIDENCE_MEDIUM,
          "ROW token indicates right of way linework."),
    _rule("token", "PROP", CATEGORY_PROPERTY_BOUNDARY, CONFIDENCE_MEDIUM,
          "Bare PROP token mapped to property lines. PROP is also used as a "
          "proposed-work modifier by some firms; a reviewer can override."),
    _rule("token", "EXST", CATEGORY_EXISTING, CONFIDENCE_MEDIUM,
          "EXST token indicates existing conditions."),
    _rule("token", "EXIST", CATEGORY_EXISTING, CONFIDENCE_MEDIUM,
          "EXIST token indicates existing conditions."),
    _rule("token", "EX", CATEGORY_EXISTING, CONFIDENCE_LOW,
          "EX token often indicates existing conditions."),
]

# Contains rules are the last tier. They preserve the reach of the original
# eight-keyword substring classifier for compound names without separators,
# for example TITLEBLOCK or STORMWATER1.
CONTAINS_RULES: list[LayerRule] = [
    _rule("contains", "WTLND", CATEGORY_WETLAND, CONFIDENCE_MEDIUM,
          "Name contains WTLND."),
    _rule("contains", "WETLAND", CATEGORY_WETLAND, CONFIDENCE_MEDIUM,
          "Name contains WETLAND."),
    _rule("contains", "STORM", CATEGORY_STORMWATER, CONFIDENCE_MEDIUM,
          "Name contains STORM."),
    _rule("contains", "GRAD", CATEGORY_GRADING, CONFIDENCE_LOW,
          "Name contains GRAD."),
    _rule("contains", "EROS", CATEGORY_EROSION, CONFIDENCE_LOW,
          "Name contains EROS."),
    _rule("contains", "UTIL", CATEGORY_UTILITIES, CONFIDENCE_LOW,
          "Name contains UTIL."),
    _rule("contains", "TITLE", CATEGORY_TITLEBLOCK, CONFIDENCE_MEDIUM,
          "Name contains TITLE."),
    _rule("contains", "LANDSCAPE", CATEGORY_LANDSCAPE, CONFIDENCE_MEDIUM,
          "Name contains LANDSCAPE."),
    _rule("contains", "NOTE", CATEGORY_NOTES, CONFIDENCE_LOW,
          "Name contains NOTE."),
]

_EXACT_RULES: dict[str, LayerRule] = {
    r.pattern: r for r in LAYER_RULES if r.kind == "exact"
}
_TOKEN_RULES: list[LayerRule] = [r for r in LAYER_RULES if r.kind == "token"]

_TOKEN_SPLIT_RE = re.compile(r"[^A-Z0-9]+")


def normalize_layer_name(layer_name: str) -> str:
    return re.sub(r"\s+", " ", (layer_name or "").strip().upper())


def tokenize_layer_name(normalized: str) -> tuple[str, ...]:
    return tuple(t for t in _TOKEN_SPLIT_RE.split(normalized) if t)


def classify_layer(
    layer_name: str,
    *,
    overrides: dict[str, str] | None = None,
) -> LayerClassification:
    """Classify one layer name.

    overrides maps a normalized layer name to a category and represents an
    explicit reviewer or project mapping. Overrides win over every rule and are
    reported with rule_kind override so the decision trail stays visible.
    """

    normalized = normalize_layer_name(layer_name)
    tokens = tokenize_layer_name(normalized)

    if not normalized:
        return LayerClassification(
            layer_name=layer_name,
            normalized_name=normalized,
            category=CATEGORY_UNKNOWN,
            confidence=CONFIDENCE_LOW,
            rule_kind="none",
            rule_pattern="",
            explanation="Empty layer name cannot be classified.",
            unknown_reason="empty_layer_name",
            tokens=tokens,
        )

    if overrides:
        override_category = overrides.get(normalized)
        if override_category:
            return LayerClassification(
                layer_name=layer_name,
                normalized_name=normalized,
                category=override_category,
                confidence=CONFIDENCE_HIGH,
                rule_kind="override",
                rule_pattern=normalized,
                explanation="Explicit reviewer or project mapping.",
                tokens=tokens,
            )

    if normalized in NEUTRAL_LAYERS:
        return LayerClassification(
            layer_name=layer_name,
            normalized_name=normalized,
            category=CATEGORY_UNKNOWN,
            confidence=CONFIDENCE_HIGH,
            rule_kind="neutral",
            rule_pattern=normalized,
            explanation=(
                "Default CAD layer with no review meaning of its own."
            ),
            unknown_reason="neutral_default_layer",
            tokens=tokens,
        )

    exact = _EXACT_RULES.get(normalized)
    if exact:
        return LayerClassification(
            layer_name=layer_name,
            normalized_name=normalized,
            category=exact.category,
            confidence=exact.confidence,
            rule_kind="exact",
            rule_pattern=exact.pattern,
            explanation=exact.explanation,
            tokens=tokens,
        )

    token_set = set(tokens)
    for rule in _TOKEN_RULES:
        if rule.pattern in token_set:
            return LayerClassification(
                layer_name=layer_name,
                normalized_name=normalized,
                category=rule.category,
                confidence=rule.confidence,
                rule_kind="token",
                rule_pattern=rule.pattern,
                explanation=rule.explanation,
                tokens=tokens,
            )

    for rule in CONTAINS_RULES:
        if rule.pattern in normalized:
            return LayerClassification(
                layer_name=layer_name,
                normalized_name=normalized,
                category=rule.category,
                confidence=rule.confidence,
                rule_kind="contains",
                rule_pattern=rule.pattern,
                explanation=rule.explanation,
                tokens=tokens,
            )

    return LayerClassification(
        layer_name=layer_name,
        normalized_name=normalized,
        category=CATEGORY_UNKNOWN,
        confidence=CONFIDENCE_LOW,
        rule_kind="none",
        rule_pattern="",
        explanation=(
            "No taxonomy rule matched. The layer keeps its inventory and "
            "needs reviewer categorization."
        ),
        unknown_reason="no_rule_matched",
        tokens=tokens,
    )


def layer_category(layer_name: str) -> str:
    """Category-only helper kept for pipeline call sites."""

    return classify_layer(layer_name).category
