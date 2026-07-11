"""Reference parser tests: supported forms and overmatch prevention."""

from __future__ import annotations

from app.services.cad.reference_parser import (
    normalize_sheet_token,
    parse_references,
)


def single(text: str):
    refs = parse_references(text)
    assert len(refs) == 1, f"Expected one reference in {text!r}, got {refs}"
    return refs[0]


class TestSheetForms:
    def test_plain_hyphenated_token(self) -> None:
        ref = single("C-3.1")
        assert ref.reference_type == "sheet_reference"
        assert ref.normalized_reference == "C-3.1"
        assert not ref.ambiguous

    def test_compact_token_with_context(self) -> None:
        ref = single("SEE SHEET C3.1")
        assert ref.normalized_reference == "C-3.1"

    def test_compact_token_without_context_is_not_matched(self) -> None:
        # No context words: C3.1 alone could be a model number or a label.
        assert parse_references("C3.1") == []

    def test_sheet_prefix(self) -> None:
        ref = single("SHEET C-3.1")
        assert ref.normalized_reference == "C-3.1"

    def test_see_sheet(self) -> None:
        ref = single("SEE SHEET C-5.0 FOR OUTLET")
        assert ref.normalized_reference == "C-5.0"

    def test_two_letter_discipline(self) -> None:
        ref = single("SEE SHEET CU-1.0")
        assert ref.normalized_reference == "CU-1.0"


class TestDetailForms:
    def test_detail_slash(self) -> None:
        ref = single("DETAIL 4/C-5.0")
        assert ref.reference_type == "detail_reference"
        assert ref.detail_number == "4"
        assert ref.sheet_token == "C-5.0"
        assert ref.normalized_reference == "DETAIL 4/C-5.0"

    def test_bare_slash_form(self) -> None:
        ref = single("4/C-5.0")
        assert ref.reference_type == "detail_reference"
        assert ref.detail_number == "4"

    def test_detail_on_sheet(self) -> None:
        ref = single("DETAIL 4 ON SHEET C-5.0")
        assert ref.reference_type == "detail_reference"
        assert ref.sheet_token == "C-5.0"

    def test_see_detail(self) -> None:
        ref = single("SEE DETAIL 4/C-5.0")
        assert ref.detail_number == "4"

    def test_sheet_comma_detail(self) -> None:
        ref = single("C-5.0, DETAIL 4")
        assert ref.reference_type == "detail_reference"
        assert ref.sheet_token == "C-5.0"
        assert ref.detail_number == "4"

    def test_ambiguous_detail(self) -> None:
        ref = single("DETAIL ?/C-4.X")
        assert ref.ambiguous
        assert ref.ambiguity_reason is not None

    def test_ambiguous_sheet_suffix(self) -> None:
        ref = single("SEE DETAIL 2/C-5.X")
        assert ref.ambiguous

    def test_detail_sheet_not_double_counted(self) -> None:
        refs = parse_references("DETAIL 3/C-5.1 TYPICAL TRENCH SECTION")
        assert len(refs) == 1
        assert refs[0].reference_type == "detail_reference"


class TestOvermatchPrevention:
    """Numbers that look reference-like but are not sheets."""

    def test_elevation(self) -> None:
        assert parse_references("ELEV 123.5") == []

    def test_invert_elevation(self) -> None:
        assert parse_references("INV EL 98.25") == []

    def test_slope(self) -> None:
        assert parse_references("SLOPE 2.0%") == []

    def test_pipe_size(self) -> None:
        assert parse_references("12 IN. DIA RCP") == []

    def test_date(self) -> None:
        assert parse_references("2026-05-01") == []

    def test_revision_number(self) -> None:
        assert parse_references("REV 2.1") == []

    def test_station_value(self) -> None:
        assert parse_references("STA 10+50.00") == []

    def test_lot_number(self) -> None:
        assert parse_references("LOT 4.1") == []

    def test_storm_frequency(self) -> None:
        assert parse_references("25-YR STORM EVENT") == []

    def test_bare_decimal(self) -> None:
        assert parse_references("3.1") == []


class TestNormalization:
    def test_normalize_inserts_hyphen(self) -> None:
        assert normalize_sheet_token("C3.1") == "C-3.1"

    def test_normalize_keeps_hyphen(self) -> None:
        assert normalize_sheet_token("C-3.1") == "C-3.1"

    def test_normalize_uppercases(self) -> None:
        assert normalize_sheet_token("c-3.1") == "C-3.1"

    def test_multiple_references_in_one_note(self) -> None:
        refs = parse_references("SEE SHEET C-3.1 AND DETAIL 4/C-5.0")
        types = {r.reference_type for r in refs}
        assert types == {"sheet_reference", "detail_reference"}
        assert len(refs) == 2
