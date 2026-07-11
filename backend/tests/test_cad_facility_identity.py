"""Facility identity parsing and conflict-rule tests.

Covers the required scenario list: Detention Basin 1 versus Infiltration
Basin 1 (must not conflict), Basin 1 versus Pond A, Detention Pond A versus
Pond A, Basin 1 versus Basin No. 1, BMP-1 versus Basin 1, same label in two
locations, different type labels at the same location, ambiguous facility
text, missing identifiers, and false-positive prevention.
"""

from __future__ import annotations

from app.services.cad.facility_identity import (
    FacilityIdentity,
    detect_facility_conflicts,
    parse_facility_label,
)


def parse(text: str, location=None) -> FacilityIdentity:
    identity = parse_facility_label(text, location=location)
    assert identity is not None, f"Expected a facility identity for {text!r}"
    return identity


class TestParsing:
    def test_detention_basin(self) -> None:
        identity = parse("DETENTION BASIN 1")
        assert identity.facility_type == "detention_basin"
        assert identity.identifier == "1"
        assert identity.is_typed

    def test_infiltration_basin(self) -> None:
        identity = parse("INFILTRATION BASIN 1")
        assert identity.facility_type == "infiltration_basin"
        assert identity.identifier == "1"

    def test_generic_basin(self) -> None:
        identity = parse("BASIN A")
        assert identity.facility_type == "unknown_stormwater_facility"
        assert identity.identifier == "A"
        assert not identity.is_typed

    def test_wet_basin_is_retention(self) -> None:
        assert parse("WET BASIN A").facility_type == "retention_basin"

    def test_identifier_aliases(self) -> None:
        assert parse("BASIN NO. 1").identifier == "1"
        assert parse("BASIN #1").identifier == "1"
        assert parse("BASIN 1").identifier == "1"

    def test_bmp_identifier(self) -> None:
        identity = parse("BMP-1")
        assert identity.identifier == "1"
        assert not identity.is_typed

    def test_missing_identifier(self) -> None:
        identity = parse("DETENTION BASIN")
        assert identity.identifier is None

    def test_outfall_and_outlet(self) -> None:
        assert parse("OUTFALL 1").facility_type == "outfall"
        assert parse("OUTLET STRUCTURE 2").facility_type == "outlet_structure"

    def test_bioretention_and_rain_garden(self) -> None:
        assert parse("BIORETENTION AREA 3").facility_type == "bioretention_area"
        assert parse("RAIN GARDEN 2").facility_type == "rain_garden"

    def test_non_facility_text_returns_none(self) -> None:
        assert parse_facility_label("SEE SHEET C-3.1") is None
        assert parse_facility_label("PROPERTY LINE") is None
        assert parse_facility_label("") is None


class TestConflictRules:
    def test_detention_vs_infiltration_same_number_is_not_a_conflict(
        self,
    ) -> None:
        """The verified simulation false positive must not recur."""

        conflicts = detect_facility_conflicts(
            [parse("DETENTION BASIN 1"), parse("INFILTRATION BASIN 1")]
        )
        assert conflicts == []

    def test_basin_1_vs_pond_a_no_conflict(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("BASIN 1"), parse("POND A")]
        )
        assert conflicts == []

    def test_detention_pond_a_vs_pond_a_flags_inconsistency(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("DETENTION POND A"), parse("POND A")]
        )
        assert len(conflicts) == 1
        assert conflicts[0].rule == "generic_and_typed_same_identifier"
        assert "reviewer" in conflicts[0].reason.lower()

    def test_basin_1_vs_basin_no_1_is_alias_not_conflict(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("BASIN 1"), parse("BASIN NO. 1")]
        )
        assert conflicts == []

    def test_bmp_1_vs_basin_1_no_conflict(self) -> None:
        # Two generic labels lack identity evidence; not flagged.
        conflicts = detect_facility_conflicts(
            [parse("BMP-1"), parse("BASIN 1")]
        )
        assert conflicts == []

    def test_generic_and_single_typed_family_flags(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("WET BASIN A"), parse("BASIN A")]
        )
        assert len(conflicts) == 1
        assert conflicts[0].rule == "generic_and_typed_same_identifier"

    def test_generic_with_two_typed_families_not_attributed(self) -> None:
        # The generic label cannot be attributed to either family.
        conflicts = detect_facility_conflicts(
            [
                parse("DETENTION BASIN 1"),
                parse("INFILTRATION BASIN 1"),
                parse("BASIN 1"),
            ]
        )
        assert conflicts == []

    def test_same_type_same_identifier_different_qualifier(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("NORTH DETENTION BASIN 2"), parse("SOUTH DETENTION BASIN 2")]
        )
        assert len(conflicts) == 1
        assert conflicts[0].rule == "same_type_different_name"

    def test_same_label_in_two_locations_is_not_a_conflict(self) -> None:
        conflicts = detect_facility_conflicts(
            [
                parse("DETENTION BASIN 1", location=(0.0, 0.0)),
                parse("DETENTION BASIN 1", location=(500.0, 500.0)),
            ]
        )
        assert conflicts == []

    def test_incompatible_types_at_same_location_flag(self) -> None:
        conflicts = detect_facility_conflicts(
            [
                parse("DETENTION BASIN 1", location=(100.0, 100.0)),
                parse("INFILTRATION BASIN 2", location=(100.2, 100.3)),
            ]
        )
        assert len(conflicts) == 1
        assert conflicts[0].rule == "incompatible_types_same_location"

    def test_incompatible_types_far_apart_do_not_flag(self) -> None:
        conflicts = detect_facility_conflicts(
            [
                parse("DETENTION BASIN 1", location=(0.0, 0.0)),
                parse("INFILTRATION BASIN 2", location=(400.0, 300.0)),
            ]
        )
        assert conflicts == []

    def test_no_identifier_labels_do_not_group(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("DETENTION BASIN"), parse("INFILTRATION BASIN")]
        )
        assert conflicts == []

    def test_conflict_carries_evidence(self) -> None:
        conflicts = detect_facility_conflicts(
            [parse("WET BASIN A"), parse("BASIN A")]
        )
        conflict = conflicts[0]
        assert conflict.identifier == "A"
        assert set(conflict.labels) == {"WET BASIN A", "BASIN A"}
        assert len(conflict.identities) == 2
        assert conflict.confidence in {"low", "medium"}
        # Review-support wording only; never a confirmed determination.
        assert "possible" in conflict.reason.lower()
        for word in ("violation", "confirmed conflict", "noncompliant"):
            assert word not in conflict.reason.lower()
