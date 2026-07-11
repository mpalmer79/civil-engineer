"""Layer taxonomy classification corpus tests.

The corpus covers exact names, hyphen and underscore variants, mixed case,
compound modifiers, ambiguous names, empty names, and overrides. The corpus
accuracy assertions track the taxonomy quality metrics recorded in the
transformation tracker.
"""

from __future__ import annotations

from app.services.cad import layer_taxonomy as tax


def classify(name: str) -> str:
    return tax.classify_layer(name).category


class TestRequiredBaselineMappings:
    """The five layers the verified simulation over-flagged as unknown."""

    def test_c_prop(self) -> None:
        assert classify("C-PROP") == "property_boundary"

    def test_c_road(self) -> None:
        assert classify("C-ROAD") == "road_alignment"

    def test_c_lots(self) -> None:
        assert classify("C-LOTS") == "lots_parcels"

    def test_c_label(self) -> None:
        assert classify("C-LABEL") == "annotation"

    def test_c_landscape(self) -> None:
        assert classify("C-LANDSCAPE") == "landscape"


class TestCommonVariations:
    def test_grading_variants(self) -> None:
        assert classify("C-GRAD") == "grading"
        assert classify("C-CONT") == "grading"
        assert classify("C-TOPO") == "grading"

    def test_storm_variants(self) -> None:
        assert classify("C-STRM") == "stormwater"
        assert classify("C-STORM") == "stormwater"
        assert classify("C-DRAN") == "stormwater"

    def test_wetland_variants(self) -> None:
        assert classify("C-WETL") == "wetland_buffer"
        assert classify("C-WTLND") == "wetland_buffer"

    def test_erosion_and_utilities(self) -> None:
        assert classify("C-EROS") == "erosion_control"
        assert classify("C-UTIL") == "utilities"

    def test_annotation_variants(self) -> None:
        assert classify("C-TEXT") == "annotation"
        assert classify("C-ANNO") == "annotation"

    def test_boundary_variants(self) -> None:
        assert classify("C-BOUND") == "property_boundary"
        assert classify("C-PARCEL") == "lots_parcels"

    def test_existing_conditions(self) -> None:
        assert classify("C-EXST") == "existing_conditions"

    def test_compound_proposed_modifiers_route_to_subject(self) -> None:
        # The subject token wins over the PROP modifier.
        assert classify("C-PROP-ROAD") == "road_alignment"
        assert classify("C-PROP-GRAD") == "grading"

    def test_existing_modifier_with_subject(self) -> None:
        assert classify("C-EXST-UTIL") == "utilities"


class TestNameForms:
    def test_underscores(self) -> None:
        assert classify("C_STORM_PIPE") == "stormwater"

    def test_mixed_case(self) -> None:
        assert classify("c-Road") == "road_alignment"

    def test_long_name(self) -> None:
        assert (
            classify("SITE-CIVIL-PROPOSED-STORM-DRAINAGE-TRUNK-LINE-2026")
            == "stormwater"
        )

    def test_compound_without_separator_uses_contains_tier(self) -> None:
        result = tax.classify_layer("TITLEBLOCK")
        assert result.category == "titleblock"
        assert result.rule_kind == "contains"

    def test_empty_name(self) -> None:
        result = tax.classify_layer("")
        assert result.category == "unknown"
        assert result.unknown_reason == "empty_layer_name"

    def test_invalid_characters_still_tokenize(self) -> None:
        assert classify("C@STORM##7") == "stormwater"


class TestUnknownAndNeutral:
    def test_ambiguous_name_stays_unknown(self) -> None:
        result = tax.classify_layer("V-MISC")
        assert result.category == "unknown"
        assert result.unknown_reason == "no_rule_matched"
        assert result.requires_human_review

    def test_neutral_default_layers(self) -> None:
        for name in ("0", "DEFPOINTS"):
            result = tax.classify_layer(name)
            assert result.category == "unknown"
            assert result.unknown_reason == "neutral_default_layer"


class TestOverrides:
    def test_override_wins_over_rules(self) -> None:
        result = tax.classify_layer(
            "C-ROAD", overrides={"C-ROAD": "grading"}
        )
        assert result.category == "grading"
        assert result.rule_kind == "override"

    def test_override_applies_to_unknown_layers(self) -> None:
        result = tax.classify_layer(
            "V-MISC", overrides={"V-MISC": "utilities"}
        )
        assert result.category == "utilities"


class TestClassificationOutput:
    def test_result_reports_rule_and_explanation(self) -> None:
        result = tax.classify_layer("C-PROP")
        assert result.rule_kind == "exact"
        assert result.rule_pattern == "C-PROP"
        assert result.confidence == "medium"
        assert "override" in result.explanation

    def test_no_conclusion_language(self) -> None:
        forbidden = ("approved", "certified", "verified", "compliant")
        for rule in tax.LAYER_RULES + tax.CONTAINS_RULES:
            lowered = rule.explanation.lower()
            for word in forbidden:
                assert word not in lowered


# Labeled corpus for the accuracy metric. Each entry is (name, expected).
CORPUS: list[tuple[str, str]] = [
    ("C-PROP", "property_boundary"),
    ("C-ROAD", "road_alignment"),
    ("C-LOTS", "lots_parcels"),
    ("C-LABEL", "annotation"),
    ("C-LANDSCAPE", "landscape"),
    ("C-GRAD", "grading"),
    ("C-CONT", "grading"),
    ("C-STRM", "stormwater"),
    ("C-DRAN", "stormwater"),
    ("C-WETL", "wetland_buffer"),
    ("C-EROS", "erosion_control"),
    ("C-UTIL", "utilities"),
    ("C-TEXT", "annotation"),
    ("C-ANNO", "annotation"),
    ("C-BOUND", "property_boundary"),
    ("C-PARCEL", "lots_parcels"),
    ("C-EXST", "existing_conditions"),
    ("C-PROP-ROAD", "road_alignment"),
    ("C-PROP-GRAD", "grading"),
    ("C-STORM", "stormwater"),
    ("C-WTLND", "wetland_buffer"),
    ("C-NOTES", "notes"),
    ("TITLEBLOCK", "titleblock"),
    ("C_STORM_PIPE", "stormwater"),
    ("c-road", "road_alignment"),
    ("C-CURB", "road_alignment"),
    ("C-SSWR", "utilities"),
    ("C-WATR", "utilities"),
    ("C-SILT-FENCE", "erosion_control"),
    ("C-TREE", "landscape"),
    ("C-BLDG", "structures"),
    ("C-SURV", "survey_control"),
    ("L-PLNT", "landscape"),
    ("V-MISC", "unknown"),
    ("XREF-STUFF", "unknown"),
    ("0", "unknown"),
    ("DEFPOINTS", "unknown"),
    ("C-ROW", "property_boundary"),
    ("C-BNDY", "property_boundary"),
    ("C-DIMS", "annotation"),
]


def test_corpus_accuracy_is_complete() -> None:
    """Every corpus entry classifies as labeled: 100 percent on this corpus.

    The corpus is the tracked metric set; a regression here is a taxonomy
    regression, not a flaky signal.
    """

    misses = [
        (name, expected, classify(name))
        for name, expected in CORPUS
        if classify(name) != expected
    ]
    assert not misses, f"Taxonomy corpus misses: {misses}"


def test_corpus_unknown_rate() -> None:
    """Only the four intentionally unknown entries stay unknown."""

    unknown = [name for name, _ in CORPUS if classify(name) == "unknown"]
    assert sorted(unknown) == ["0", "DEFPOINTS", "V-MISC", "XREF-STUFF"]
