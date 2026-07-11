"""Structured stormwater facility identity and label-conflict rules.

The earlier basin-conflict heuristic keyed only on the trailing identifier
token, so DETENTION BASIN 1 and INFILTRATION BASIN 1 were flagged as a
conflict even though they are different facility types that happen to share
the number 1. This module parses each label into a structured identity
(facility type, identifier, normalized name) and only raises a possible
naming inconsistency when there is meaningful disagreement.

Every result is a review-support observation. When identity is uncertain the
finding says possible naming inconsistency and needs reviewer confirmation.
Nothing here claims a confirmed design conflict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FACILITY_UNKNOWN = "unknown_stormwater_facility"

# Ordered (phrase, facility_type) table. Longer, more specific phrases first
# so DETENTION BASIN wins over BASIN and DRY POND wins over POND.
_FACILITY_PHRASES: list[tuple[str, str]] = [
    ("DETENTION BASIN", "detention_basin"),
    ("DETENTION POND", "detention_basin"),
    ("DRY DETENTION", "detention_basin"),
    ("RETENTION BASIN", "retention_basin"),
    ("RETENTION POND", "retention_basin"),
    ("WET BASIN", "retention_basin"),
    ("WET POND", "retention_basin"),
    ("INFILTRATION BASIN", "infiltration_basin"),
    ("INFILTRATION TRENCH", "infiltration_basin"),
    ("BIORETENTION", "bioretention_area"),
    ("RAIN GARDEN", "rain_garden"),
    ("UNDERGROUND STORAGE", "underground_storage"),
    ("UNDERGROUND DETENTION", "underground_storage"),
    ("OUTLET STRUCTURE", "outlet_structure"),
    ("OUTLET CONTROL", "outlet_structure"),
    ("OUTFALL", "outfall"),
    ("SWALE", "swale"),
    ("FOREBAY", "forebay"),
    ("POND", "pond"),
    ("BASIN", FACILITY_UNKNOWN),
    ("BMP", FACILITY_UNKNOWN),
]

# Identifier forms: "1", "NO. 1", "#1", "A", "1A". Matched at the end of the
# label after the facility phrase.
_IDENTIFIER_RE = re.compile(
    r"(?:\bNO\.?\s*|#\s*|-\s*)?([A-Z]?\d+[A-Z]?|\b[A-Z])\s*$"
)

# Generic facility words that mean the label is untyped rather than typed.
# pond is treated as generic on purpose: a bare POND A label is routinely an
# informal name for a typed facility (DETENTION POND A), so it participates in
# the generic-plus-typed rule instead of counting as its own type.
_GENERIC_TYPES = {FACILITY_UNKNOWN, "pond"}


@dataclass(frozen=True)
class FacilityIdentity:
    """Structured identity parsed from one stormwater facility label."""

    source_text: str
    normalized_label: str
    facility_type: str
    identifier: str | None
    name_qualifier: str
    location: tuple[float, float] | None = None

    @property
    def is_typed(self) -> bool:
        return self.facility_type not in _GENERIC_TYPES

    @property
    def identity_key(self) -> tuple[str, str | None]:
        return (self.facility_type, self.identifier)


@dataclass(frozen=True)
class FacilityConflict:
    """A possible naming inconsistency between two facility labels."""

    rule: str
    identifier: str | None
    labels: tuple[str, ...]
    identities: tuple[FacilityIdentity, ...]
    reason: str
    confidence: str


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().upper())


def parse_facility_label(
    text: str, *, location: tuple[float, float] | None = None
) -> FacilityIdentity | None:
    """Parse a stormwater facility label into a structured identity.

    Returns None when the text does not look like a facility label at all.
    """

    normalized = _normalize(text)
    if not normalized:
        return None

    facility_type = None
    matched_phrase = ""
    for phrase, ftype in _FACILITY_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", normalized):
            facility_type = ftype
            matched_phrase = phrase
            break
    if facility_type is None:
        return None

    identifier = None
    id_match = _IDENTIFIER_RE.search(normalized)
    if id_match:
        candidate = id_match.group(1)
        # Reject an identifier that is just part of the phrase itself.
        if candidate and not matched_phrase.endswith(candidate):
            identifier = candidate

    # The qualifier is everything before the matched phrase, for example WET
    # in WET BASIN A when only BASIN matched, or an owner prefix.
    phrase_index = normalized.find(matched_phrase)
    name_qualifier = normalized[:phrase_index].strip()

    return FacilityIdentity(
        source_text=text,
        normalized_label=normalized,
        facility_type=facility_type,
        identifier=identifier,
        name_qualifier=name_qualifier,
        location=location,
    )


def _alias_equivalent(a: FacilityIdentity, b: FacilityIdentity) -> bool:
    """True when two labels are alias spellings of the same identity.

    BASIN 1, BASIN NO. 1, and BASIN #1 normalize to the same type and
    identifier with the same qualifier, so they are not a conflict.
    """

    return (
        a.facility_type == b.facility_type
        and a.identifier == b.identifier
        and a.name_qualifier == b.name_qualifier
    )


def detect_facility_conflicts(
    labels: list[FacilityIdentity],
) -> list[FacilityConflict]:
    """Detect possible naming inconsistencies among facility labels.

    Rules, all of which need meaningful disagreement:

    1. same_type_different_name: two labels with the same explicit facility
       type and identifier but materially different qualifiers.
    2. generic_and_typed_same_identifier: an untyped label (BASIN 1) shares an
       identifier with exactly one typed family (WET BASIN 1). The generic
       label may be an inconsistent name for the typed facility.

    3. incompatible_types_same_location: two labels with different explicit
       facility types placed at effectively the same drawing location, which
       suggests one facility carries two type labels.

    Never flagged: different explicit facility types sharing an identifier
    (DETENTION BASIN 1 versus INFILTRATION BASIN 1) at separate locations,
    and generic labels with no identifier evidence.
    """

    conflicts: list[FacilityConflict] = []

    by_identifier: dict[str, list[FacilityIdentity]] = {}
    for identity in labels:
        if identity.identifier is None:
            continue
        by_identifier.setdefault(identity.identifier, []).append(identity)

    for identifier, group in sorted(by_identifier.items()):
        typed = [i for i in group if i.is_typed]
        generic = [i for i in group if not i.is_typed]

        # Rule 1: same explicit type, same identifier, different qualifier or
        # spelling that is not an alias.
        by_type: dict[str, list[FacilityIdentity]] = {}
        for identity in typed:
            by_type.setdefault(identity.facility_type, []).append(identity)
        for ftype, members in sorted(by_type.items()):
            distinct = []
            for member in members:
                if not any(_alias_equivalent(member, seen) for seen in distinct):
                    distinct.append(member)
            if len(distinct) > 1:
                conflicts.append(
                    FacilityConflict(
                        rule="same_type_different_name",
                        identifier=identifier,
                        labels=tuple(
                            sorted(i.normalized_label for i in distinct)
                        ),
                        identities=tuple(distinct),
                        reason=(
                            f"Labels of the same facility type ({ftype}) share "
                            f"identifier '{identifier}' but use materially "
                            "different names. Possible naming inconsistency; "
                            "needs reviewer confirmation."
                        ),
                        confidence="medium",
                    )
                )

        # Rule 2: a generic label plus exactly one typed family with the same
        # identifier. Two or more typed families mean the generic label lacks
        # enough identity evidence to attribute, so it is not flagged.
        typed_families = {i.facility_type for i in typed}
        if generic and len(typed_families) == 1:
            typed_family = sorted(typed_families)[0]
            distinct_labels = sorted(
                {i.normalized_label for i in generic}
                | {i.normalized_label for i in typed}
            )
            if len(distinct_labels) > 1:
                conflicts.append(
                    FacilityConflict(
                        rule="generic_and_typed_same_identifier",
                        identifier=identifier,
                        labels=tuple(distinct_labels),
                        identities=tuple(generic + typed),
                        reason=(
                            f"A generic label shares identifier '{identifier}' "
                            f"with a {typed_family} label. The generic label "
                            "may be an inconsistent name for the same "
                            "facility. Possible naming inconsistency; needs "
                            "reviewer confirmation."
                        ),
                        confidence="low",
                    )
                )

    # Rule 3: incompatible explicit types at effectively the same location.
    located = [
        i for i in labels if i.is_typed and i.location is not None
    ]
    tolerance = 1.0
    seen_pairs: set[tuple[str, str]] = set()
    for index, first in enumerate(located):
        for second in located[index + 1:]:
            if first.facility_type == second.facility_type:
                continue
            pair_key = tuple(
                sorted((first.normalized_label, second.normalized_label))
            )
            if pair_key in seen_pairs:
                continue
            dx = abs(first.location[0] - second.location[0])
            dy = abs(first.location[1] - second.location[1])
            if dx <= tolerance and dy <= tolerance:
                seen_pairs.add(pair_key)
                conflicts.append(
                    FacilityConflict(
                        rule="incompatible_types_same_location",
                        identifier=first.identifier or second.identifier,
                        labels=pair_key,
                        identities=(first, second),
                        reason=(
                            "Two different facility type labels sit at "
                            "effectively the same drawing location. One "
                            "facility may carry two type labels. Possible "
                            "naming inconsistency; needs reviewer "
                            "confirmation."
                        ),
                        confidence="medium",
                    )
                )

    return conflicts
