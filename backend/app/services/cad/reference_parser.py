"""Sheet and detail reference parsing for extracted CAD text.

Parses plan text into normalized sheet and detail references without
overmatching. A bare decimal number is never treated as a sheet: a match needs
either the strong discipline-hyphen pattern (C-3.1) or explicit context words
(SHEET, SEE, DETAIL, DTL) around a compact form (C3.1).

Supported forms include:

* C-3.1
* C3.1 (with sheet context)
* SHEET C-3.1, SEE SHEET C-3.1
* DETAIL 4/C-5.0, 4/C-5.0, SEE DETAIL 4/C-5.0
* DETAIL 4 ON SHEET C-5.0
* C-5.0, DETAIL 4
* DETAIL ?/C-4.X (explicitly ambiguous)

Matching a reference is text identification, not engineering verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Strong sheet token: discipline letter(s), hyphen, sheet number with decimal.
SHEET_TOKEN_RE = re.compile(r"\b([A-Z]{1,2}-\d{1,2}\.\d[0-9A-Z]?)\b")
# Compact sheet token without a hyphen. Only used when context words appear.
COMPACT_SHEET_TOKEN_RE = re.compile(r"\b([A-Z]{1,2})(\d{1,2}\.\d[0-9A-Z]?)\b")
# Ambiguous sheet token, for example C-4.X where the suffix is not a digit.
AMBIGUOUS_SHEET_RE = re.compile(r"\b([A-Z]{1,2}-\d{1,2}\.[A-Z?])\b")

# Detail forms.
DETAIL_SLASH_RE = re.compile(
    r"(?:\bDETAIL\s+|\bDTL\.?\s+|(?<![\w.]))([0-9?]{1,3})\s*/\s*"
    r"([A-Z]{1,2}-\d{1,2}\.[0-9A-Z?])\b"
)
DETAIL_ON_SHEET_RE = re.compile(
    r"\bDETAIL\s+([0-9?]{1,3})\s+ON\s+SHEET\s+([A-Z]{1,2}-\d{1,2}\.[0-9A-Z?])\b"
)
SHEET_COMMA_DETAIL_RE = re.compile(
    r"\b([A-Z]{1,2}-\d{1,2}\.[0-9A-Z?])\s*,\s*DETAIL\s+([0-9?]{1,3})\b"
)

_CONTEXT_WORDS_RE = re.compile(r"\b(SHEET|SHT|SEE|DETAIL|DTL)\b")

# Negative context: numbers that commonly look reference-like but are not.
# These are checked around compact matches to avoid claiming elevations,
# slopes, pipe sizes, stations, dates, revisions, or storm frequencies.
_NEGATIVE_CONTEXT_RE = re.compile(
    r"\b(ELEV|EL|INV|RIM|SLOPE|GRADE|STA|STATION|LOT|REV|YR|YEAR|STORM\s+EVENT"
    r"|IN\.|INCH|DIA|%)\b"
)


@dataclass(frozen=True)
class ParsedReference:
    """One normalized reference extracted from a text value."""

    raw_text: str
    reference_type: str  # sheet_reference or detail_reference
    sheet_token: str
    detail_number: str | None
    normalized_reference: str
    ambiguous: bool
    ambiguity_reason: str | None


def normalize_sheet_token(token: str) -> str:
    """Normalize a sheet token to the hyphenated uppercase form."""

    cleaned = re.sub(r"\s+", "", (token or "").upper())
    match = re.fullmatch(r"([A-Z]{1,2})-?(\d{1,2}\.[0-9A-Z?]+)", cleaned)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return cleaned


def _sheet_is_ambiguous(token: str) -> bool:
    suffix = token.split(".")[-1] if "." in token else token
    return not suffix[:1].isdigit()


def parse_references(text: str) -> list[ParsedReference]:
    """Parse all sheet and detail references from one text value."""

    normalized_text = re.sub(r"\s+", " ", (text or "").strip().upper())
    if not normalized_text:
        return []

    results: list[ParsedReference] = []
    claimed_spans: list[tuple[int, int]] = []

    def claim(start: int, end: int) -> None:
        claimed_spans.append((start, end))

    def overlaps(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in claimed_spans)

    def add_detail(
        raw: str, detail_number: str, sheet_token: str, start: int, end: int
    ) -> None:
        claim(start, end)
        sheet = normalize_sheet_token(sheet_token)
        ambiguous = "?" in detail_number or _sheet_is_ambiguous(sheet)
        reason = None
        if "?" in detail_number:
            reason = "Detail number is unreadable or unresolved."
        elif _sheet_is_ambiguous(sheet):
            reason = "Sheet suffix is not a digit, so the sheet is unresolved."
        results.append(
            ParsedReference(
                raw_text=raw,
                reference_type="detail_reference",
                sheet_token=sheet,
                detail_number=detail_number,
                normalized_reference=f"DETAIL {detail_number}/{sheet}",
                ambiguous=ambiguous,
                ambiguity_reason=reason,
            )
        )

    for pattern in (DETAIL_ON_SHEET_RE, DETAIL_SLASH_RE):
        for match in pattern.finditer(normalized_text):
            if overlaps(match.start(), match.end()):
                continue
            detail_number, sheet_token = match.group(1), match.group(2)
            add_detail(
                match.group(0), detail_number, sheet_token,
                match.start(), match.end(),
            )

    for match in SHEET_COMMA_DETAIL_RE.finditer(normalized_text):
        if overlaps(match.start(), match.end()):
            continue
        sheet_token, detail_number = match.group(1), match.group(2)
        add_detail(
            match.group(0), detail_number, sheet_token,
            match.start(), match.end(),
        )

    has_context = bool(_CONTEXT_WORDS_RE.search(normalized_text))
    has_negative = bool(_NEGATIVE_CONTEXT_RE.search(normalized_text))

    def add_sheet(raw: str, token: str, start: int, end: int) -> None:
        claim(start, end)
        sheet = normalize_sheet_token(token)
        ambiguous = _sheet_is_ambiguous(sheet)
        results.append(
            ParsedReference(
                raw_text=raw,
                reference_type="sheet_reference",
                sheet_token=sheet,
                detail_number=None,
                normalized_reference=sheet,
                ambiguous=ambiguous,
                ambiguity_reason=(
                    "Sheet suffix is not a digit, so the sheet is unresolved."
                    if ambiguous
                    else None
                ),
            )
        )

    # Strong hyphenated tokens stand on their own.
    for match in SHEET_TOKEN_RE.finditer(normalized_text):
        if overlaps(match.start(), match.end()):
            continue
        add_sheet(match.group(0), match.group(1), match.start(), match.end())

    # Ambiguous hyphenated tokens (C-4.X) need sheet context to be reported
    # as sheet references; inside detail forms they are handled above.
    if has_context:
        for match in AMBIGUOUS_SHEET_RE.finditer(normalized_text):
            if overlaps(match.start(), match.end()):
                continue
            add_sheet(
                match.group(0), match.group(1), match.start(), match.end()
            )

    # Compact tokens (C3.1) require context words and no negative context.
    if has_context and not has_negative:
        for match in COMPACT_SHEET_TOKEN_RE.finditer(normalized_text):
            if overlaps(match.start(), match.end()):
                continue
            token = f"{match.group(1)}-{match.group(2)}"
            add_sheet(match.group(0), token, match.start(), match.end())

    return results
