"""Generate the synthetic Brookside Meadows proof-of-concept DXF.

Produces a structurally valid, AutoCAD-compatible R2010 DXF representing a
conceptual 47-lot subdivision. The drawing is synthetic review-support data:
the geometry is conceptual, is not surveyed, is not georeferenced, and is not
suitable for construction. It exists so the DXF intake pipeline can be proven
against a drawing with realistic civil content.

Deterministic on purpose: all coordinates are computed from fixed loops, the
volatile DXF header values (creation dates, GUIDs) are pinned to constants,
and entity order is fixed, so regenerating the file produces identical bytes.

Contents:

* 47 conceptual lots with lot number labels
* road alignment with a cul-de-sac (polyline, arc, circle)
* grading contours (polylines and splines) with elevation labels
* wetland boundary and buffer with a buffer label
* detention basin outline with hatch, infiltration basin outline
* storm pipes, an outfall point, erosion controls, utility lines
* facility labels including DETENTION BASIN 1 and INFILTRATION BASIN 1
  (intentionally sharing the number 1 without being the same facility),
  WET POND A plus POND A (an intentional naming inconsistency), and
  NORTH and SOUTH DETENTION BASIN 2 (a second intentional inconsistency)
* sheet references C-3.1 and C-5.0, detail reference DETAIL 4/C-5.0,
  an intentionally missing sheet C-9.9, and an intentionally ambiguous
  DETAIL ?/C-4.X
* five reusable blocks and a paper-space title layout
* four intentionally unclassifiable layers

Run from the repository root: python scripts/generate_brookside_proof_dxf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "public"
    / "proof-of-concept"
    / "dxf"
    / "brookside_meadows_realistic_submission.dxf"
)

FIXTURE_VERSION = "brookside-proof-v1"

# Classified layers (10) plus intentionally unknown layers (4) plus the
# default layer 0 gives the 15-layer inventory.
CLASSIFIED_LAYERS = [
    "C-PROP",
    "C-ROAD",
    "C-LOTS",
    "C-LABEL",
    "C-LANDSCAPE",
    "C-GRAD",
    "C-STRM",
    "C-WETL",
    "C-EROS",
    "C-UTIL",
]
# Three intentionally unclassifiable layers. With the default layers 0 and
# Defpoints plus the ten classified layers, the drawing has 15 layers.
UNKNOWN_LAYERS = ["V-MISC", "X-EXPORT", "DRAFT-01"]


def _text(space, value: str, layer: str, x: float, y: float) -> None:
    space.add_text(
        value,
        dxfattribs={"layer": layer, "height": 2.0, "insert": (x, y)},
    )


def build_document():
    import ezdxf

    doc = ezdxf.new("R2010")

    # Pin volatile header values so regeneration is byte-identical.
    doc.header["$INSUNITS"] = 2  # feet, declared, never assumed downstream
    doc.header["$TDCREATE"] = 2461132.5
    doc.header["$TDUCREATE"] = 2461132.5
    doc.header["$TDUPDATE"] = 2461132.5
    doc.header["$TDUUPDATE"] = 2461132.5
    doc.header["$FINGERPRINTGUID"] = "{BROOKSIDE-PROOF-0000-0000-000000000001}"
    doc.header["$VERSIONGUID"] = "{BROOKSIDE-PROOF-0000-0000-000000000002}"

    for name in CLASSIFIED_LAYERS + UNKNOWN_LAYERS:
        doc.layers.add(name)

    # Blocks (5): reusable CAD symbols.
    titleblock = doc.blocks.new("TITLEBLOCK_FRAME")
    titleblock.add_lwpolyline(
        [(0, 0), (180, 0), (180, 30), (0, 30), (0, 0)],
        dxfattribs={"layer": "C-LABEL"},
    )
    titleblock.add_text(
        "BROOKSIDE MEADOWS PRELIMINARY SUBDIVISION PLAN",
        dxfattribs={"layer": "C-LABEL", "height": 3.0, "insert": (5, 20)},
    )
    titleblock.add_text(
        "SYNTHETIC REVIEW-SUPPORT DRAWING, NOT FOR CONSTRUCTION",
        dxfattribs={"layer": "C-LABEL", "height": 2.0, "insert": (5, 10)},
    )

    lot_marker = doc.blocks.new("LOT_MARKER")
    lot_marker.add_circle((0, 0), radius=1.5, dxfattribs={"layer": "C-LOTS"})
    lot_marker.add_point((0, 0), dxfattribs={"layer": "C-LOTS"})

    manhole = doc.blocks.new("STORM_MANHOLE")
    manhole.add_circle((0, 0), radius=2.0, dxfattribs={"layer": "C-STRM"})
    manhole.add_line((-2, 0), (2, 0), dxfattribs={"layer": "C-STRM"})

    tree = doc.blocks.new("TREE_SYMBOL")
    tree.add_circle((0, 0), radius=4.0, dxfattribs={"layer": "C-LANDSCAPE"})

    north_arrow = doc.blocks.new("NORTH_ARROW")
    north_arrow.add_lwpolyline(
        [(0, 0), (3, -8), (0, -5), (-3, -8), (0, 0)],
        dxfattribs={"layer": "C-LABEL"},
    )
    north_arrow.add_text(
        "N", dxfattribs={"layer": "C-LABEL", "height": 3.0, "insert": (-1, 2)}
    )

    msp = doc.modelspace()

    # Property boundary (1 polyline).
    msp.add_lwpolyline(
        [(0, 0), (1000, 0), (1000, 700), (0, 700), (0, 0)],
        dxfattribs={"layer": "C-PROP"},
    )

    # 47 conceptual lots in three tiers along the road corridor, each with a
    # lot polyline and a lot number label (47 polylines + 47 texts).
    lot_index = 0
    for tier, (y0, y1) in enumerate([(40, 160), (240, 360), (440, 560)]):
        count = 16 if tier < 2 else 15
        for column in range(count):
            x0 = 30 + column * 58
            x1 = x0 + 50
            msp.add_lwpolyline(
                [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                dxfattribs={"layer": "C-LOTS"},
            )
            lot_index += 1
            _text(
                msp,
                f"LOT {lot_index}",
                "C-LABEL",
                x0 + 8,
                (y0 + y1) / 2,
            )

    # Road alignment (3 entities): centerline polyline, cul-de-sac arc and
    # bulb circle.
    msp.add_lwpolyline(
        [(0, 200), (700, 200), (860, 240)],
        dxfattribs={"layer": "C-ROAD"},
    )
    msp.add_arc(
        (880, 250), radius=45, start_angle=200, end_angle=340,
        dxfattribs={"layer": "C-ROAD"},
    )
    msp.add_circle((880, 250), radius=38, dxfattribs={"layer": "C-ROAD"})

    # Grading contours (8 entities: 6 polylines, 2 splines) with 8 elevation
    # labels.
    for index in range(6):
        base = 380 + index * 18
        msp.add_lwpolyline(
            [(20, base), (300, base + 10), (620, base - 6), (980, base + 4)],
            dxfattribs={"layer": "C-GRAD"},
        )
    msp.add_spline(
        [(20, 500), (260, 516), (540, 498), (980, 510)],
        dxfattribs={"layer": "C-GRAD"},
    )
    msp.add_spline(
        [(20, 530), (300, 544), (600, 526), (980, 540)],
        dxfattribs={"layer": "C-GRAD"},
    )
    for index in range(8):
        _text(
            msp,
            str(320 + index * 2),
            "C-LABEL",
            40 + index * 15,
            382 + index * 18,
        )

    # Wetland boundary and buffer (2 polylines) plus buffer label.
    msp.add_lwpolyline(
        [(40, 600), (180, 640), (330, 620), (420, 660), (520, 630)],
        dxfattribs={"layer": "C-WETL"},
    )
    msp.add_lwpolyline(
        [(30, 570), (180, 610), (330, 590), (430, 630), (540, 600)],
        dxfattribs={"layer": "C-WETL"},
    )
    _text(msp, "WETLAND BUFFER 50 FT", "C-WETL", 60, 585)

    # Detention basin (polyline plus hatch) and infiltration basin (polyline).
    detention_outline = [(700, 560), (840, 560), (840, 660), (700, 660)]
    msp.add_lwpolyline(
        detention_outline + [detention_outline[0]],
        dxfattribs={"layer": "C-STRM"},
    )
    hatch = msp.add_hatch(dxfattribs={"layer": "C-STRM"})
    hatch.paths.add_polyline_path(detention_outline, is_closed=True)
    msp.add_lwpolyline(
        [(560, 580), (650, 580), (650, 650), (560, 650), (560, 580)],
        dxfattribs={"layer": "C-STRM"},
    )

    # Storm pipes (4 lines) and outfall (1 point).
    msp.add_line((770, 560), (770, 420), dxfattribs={"layer": "C-STRM"})
    msp.add_line((770, 420), (500, 380), dxfattribs={"layer": "C-STRM"})
    msp.add_line((500, 380), (240, 380), dxfattribs={"layer": "C-STRM"})
    msp.add_line((605, 580), (605, 470), dxfattribs={"layer": "C-STRM"})
    msp.add_point((960, 640), dxfattribs={"layer": "C-STRM"})

    # Erosion controls (2 polylines).
    msp.add_lwpolyline(
        [(10, 20), (990, 20)], dxfattribs={"layer": "C-EROS"}
    )
    msp.add_lwpolyline(
        [(10, 680), (990, 680)], dxfattribs={"layer": "C-EROS"}
    )

    # Utilities (4 lines).
    msp.add_line((0, 190), (1000, 190), dxfattribs={"layer": "C-UTIL"})
    msp.add_line((0, 185), (1000, 185), dxfattribs={"layer": "C-UTIL"})
    msp.add_line((0, 180), (1000, 180), dxfattribs={"layer": "C-UTIL"})
    msp.add_line((0, 175), (1000, 175), dxfattribs={"layer": "C-UTIL"})

    # One stray entity on each intentionally unknown layer (4 lines).
    for index, layer in enumerate(UNKNOWN_LAYERS):
        msp.add_line(
            (900, 30 + index * 8),
            (990, 30 + index * 8),
            dxfattribs={"layer": layer},
        )

    # Facility labels (9 texts). DETENTION BASIN 1 and INFILTRATION BASIN 1
    # intentionally share the number 1; they are different facility types and
    # must not be flagged as the same facility. Three intentional naming
    # inconsistencies exercise the three conflict rules: WET POND A versus
    # POND A (generic plus typed), NORTH versus SOUTH DETENTION BASIN 2
    # (same type, different names), and BIORETENTION AREA 3 versus RAIN
    # GARDEN 3 placed at effectively the same location (incompatible types,
    # same location).
    _text(msp, "DETENTION BASIN 1", "C-LABEL", 720, 610)
    _text(msp, "INFILTRATION BASIN 1", "C-LABEL", 566, 615)
    _text(msp, "WET POND A", "C-LABEL", 720, 585)
    _text(msp, "POND A", "C-LABEL", 750, 573)
    _text(msp, "NORTH DETENTION BASIN 2", "C-LABEL", 60, 660)
    _text(msp, "SOUTH DETENTION BASIN 2", "C-LABEL", 60, 40)
    _text(msp, "OUTLET STRUCTURE 1", "C-LABEL", 830, 570)
    _text(msp, "BIORETENTION AREA 3", "C-LABEL", 400, 610)
    _text(msp, "RAIN GARDEN 3", "C-LABEL", 400.5, 610.5)

    # Reference notes (5 texts): two matched sheets, one matched detail, one
    # intentionally missing sheet, one intentionally ambiguous detail.
    _text(msp, "SEE SHEET C-3.1 FOR BASIN OUTLET DETAIL", "C-LABEL", 40, 130)
    _text(msp, "SEE SHEET C-5.0 FOR STORM PROFILES", "C-LABEL", 40, 120)
    _text(msp, "SEE DETAIL 4/C-5.0 FOR OUTLET STRUCTURE", "C-LABEL", 40, 110)
    _text(msp, "SEE SHEET C-9.9 FOR OFFSITE DRAINAGE", "C-LABEL", 40, 100)
    _text(msp, "DETAIL ?/C-4.X RIPRAP APRON", "C-LABEL", 40, 90)

    # Outfall and invert labels (2 texts). INV 638.2 is a deliberate negative
    # case: an elevation the reference parser must not claim as a sheet.
    _text(msp, "OUTFALL 1", "C-LABEL", 950, 650)
    _text(msp, "INV 638.2", "C-LABEL", 950, 630)

    # General annotation (8 texts).
    _text(msp, "BROOKSIDE MEADOWS", "C-LABEL", 40, 60)
    _text(msp, "TOWN OF HARTWELL", "C-LABEL", 40, 50)
    _text(msp, "MEADOW LANE", "C-LABEL", 300, 205)
    _text(msp, "HARTWELL WAY", "C-LABEL", 820, 260)
    _text(msp, "SILT FENCE", "C-EROS", 100, 24)
    _text(msp, "SILT FENCE", "C-EROS", 100, 676)
    _text(msp, "CONSTRUCTION ENTRANCE", "C-EROS", 500, 26)
    _text(msp, "STABILIZED ACCESS", "C-EROS", 500, 14)

    # Landscape tree symbols (2 inserts).
    msp.add_blockref("TREE_SYMBOL", (150, 620), dxfattribs={"layer": "C-LANDSCAPE"})
    msp.add_blockref("TREE_SYMBOL", (260, 640), dxfattribs={"layer": "C-LANDSCAPE"})

    # Lot markers (3 inserts) and storm manholes (3 inserts).
    msp.add_blockref("LOT_MARKER", (55, 100), dxfattribs={"layer": "C-LOTS"})
    msp.add_blockref("LOT_MARKER", (55, 300), dxfattribs={"layer": "C-LOTS"})
    msp.add_blockref("LOT_MARKER", (55, 500), dxfattribs={"layer": "C-LOTS"})
    msp.add_blockref("STORM_MANHOLE", (770, 420), dxfattribs={"layer": "C-STRM"})
    msp.add_blockref("STORM_MANHOLE", (500, 380), dxfattribs={"layer": "C-STRM"})
    msp.add_blockref("STORM_MANHOLE", (605, 470), dxfattribs={"layer": "C-STRM"})

    # Titleblock and north arrow (2 inserts).
    msp.add_blockref("TITLEBLOCK_FRAME", (760, 40), dxfattribs={"layer": "C-LABEL"})
    msp.add_blockref(
        "NORTH_ARROW",
        (960, 120),
        dxfattribs={"layer": "C-LABEL", "xscale": 2, "yscale": 2},
    )

    # Paper-space title layout so the parser's model and paper space
    # distinction has content to inventory.
    layout = doc.layout("Layout1")
    layout.add_text(
        "BROOKSIDE MEADOWS TITLE SHEET (SYNTHETIC)",
        dxfattribs={"layer": "C-LABEL", "height": 4.0, "insert": (10, 20)},
    )
    layout.add_lwpolyline(
        [(0, 0), (280, 0), (280, 200), (0, 200), (0, 0)],
        dxfattribs={"layer": "C-LABEL"},
    )

    return doc


import io
import re


def _normalize_dxf_text(text: str) -> str:
    """Pin the volatile values ezdxf rewrites at save time.

    ezdxf refreshes $TDUPDATE, $TDUUPDATE, $VERSIONGUID, and its own
    written-by metadata timestamp on every export. Normalizing them keeps
    regeneration byte-identical without touching any drawing content.
    """

    text = re.sub(
        r"(\$TDUPDATE\r?\n\s*40\r?\n)[^\r\n]+",
        r"\g<1>2461132.5",
        text,
    )
    text = re.sub(
        r"(\$TDUUPDATE\r?\n\s*40\r?\n)[^\r\n]+",
        r"\g<1>2461132.5",
        text,
    )
    text = re.sub(
        r"(\$VERSIONGUID\r?\n\s*2\r?\n)[^\r\n]+",
        r"\g<1>{BROOKSIDE-PROOF-0000-0000-000000000002}",
        text,
    )
    text = re.sub(
        r"(\d+\.\d+\.\d+) @ [0-9T:.+\-]+",
        r"\g<1> @ 2026-01-01T00:00:00+00:00",
        text,
    )
    return _sort_classes_section(text)


def _sort_classes_section(text: str) -> str:
    """Sort CLASS records by name.

    ezdxf emits the CLASSES section in per-process hash order, which is the
    last source of nondeterminism. Sorting the records is safe: readers treat
    the section as an unordered registry.
    """

    newline = "\r\n" if "\r\n" in text[:200] else "\n"
    section_start = text.find(f"CLASSES{newline}")
    if section_start == -1:
        return text
    body_start = section_start + len(f"CLASSES{newline}")
    endsec = text.find(f"  0{newline}ENDSEC", body_start)
    if endsec == -1:
        return text
    body = text[body_start:endsec]
    marker = f"  0{newline}CLASS{newline}"
    records = [r for r in body.split(marker) if r]
    records.sort()
    rebuilt = "".join(marker + record for record in records)
    return text[:body_start] + rebuilt + text[endsec:]


def build_dxf_text() -> str:
    doc = build_document()
    buffer = io.StringIO()
    doc.write(buffer)
    return _normalize_dxf_text(buffer.getvalue())


def write_dxf(output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_dxf_text(), encoding="utf-8")
    return output


if __name__ == "__main__":
    target = (
        Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    )
    written = write_dxf(target)
    print(f"Wrote {written} ({FIXTURE_VERSION})")
