"""Generate the synthetic Brookside Meadows resubmittal (round 2) DXF fixture.

This script writes a small, safe-to-parse DXF file used by the Phase 13 revision
comparison demo and tests. It represents a second review round (a resubmittal)
of the Phase 11 Brookside Meadows sample. The drawing is synthetic review-support
seed data. It is not a real survey or engineering drawing and contains no
georeferenced coordinates.

Relative to the round 1 fixture (`brookside_meadows.dxf`), this revision
intentionally:

* drops the reference to missing sheet C-9.9 (a prior missing-sheet item appears
  addressed for review)
* replaces the ambiguous detail callout with a clear DETAIL 4/C-5.2 reference
* keeps the WET BASIN A / BASIN A possible label conflict (a carried-forward item)
* adds a new pipe label P-15 and removes pipe label P-7
* adds a new erosion-control layer C-EROS2
* adds a new reference to a still-missing sheet C-8.8

These differences let the revision comparison surface added, removed, changed,
unchanged, and carried-forward references from extracted DXF metadata only. The
comparison never verifies CAD or validates engineering design.

Run with: python -m app.cad_samples.generate_sample_r2
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

OUTPUT = Path(__file__).resolve().parent / "brookside_meadows_r2.dxf"

# Civil-style layers. C-EROS2 is new in this round; V-MISC remains uncategorized.
LAYERS = [
    "C-STORM",
    "C-GRAD",
    "C-EROS",
    "C-EROS2",
    "C-UTIL",
    "C-WTLND",
    "TITLEBLOCK",
    "C-NOTES",
    "V-MISC",
]

# (layer, text, x, y) text entities placed on the model space.
TEXTS = [
    ("TITLEBLOCK", "BROOKSIDE MEADOWS", 10, 95),
    ("TITLEBLOCK", "TOWN OF HARTWELL", 10, 92),
    ("TITLEBLOCK", "SHEET C-2.0", 10, 89),
    ("C-NOTES", "SEE SHEET C-3.1 FOR BASIN OUTLET DETAIL", 10, 80),
    # C-9.9 is still referenced and still has no matching plan sheet, so the
    # missing-sheet item carries forward to this round.
    ("C-NOTES", "SEE SHEET C-9.9 FOR OFFSITE DRAINAGE", 10, 77),
    ("C-NOTES", "DETAIL 3/C-5.1 TYPICAL TRENCH SECTION", 10, 74),
    # Ambiguous headwall detail clarified to a concrete sheet reference.
    ("C-NOTES", "DETAIL 4/C-5.2 HEADWALL DETAIL", 10, 71),
    # New reference to a still-missing sheet.
    ("C-NOTES", "SEE SHEET C-8.8 FOR PHASING PLAN", 10, 68),
    ("C-STORM", "P-12", 30, 60),
    # P-7 removed; P-15 added.
    ("C-STORM", "P-15", 35, 58),
    ("C-STORM", "WET BASIN A", 50, 55),
    ("C-STORM", "BASIN A", 52, 52),
    ("C-STORM", "DETENTION BASIN 1", 60, 50),
    ("C-STORM", "OUTFALL 1", 70, 45),
    ("C-STORM", "OF-1", 72, 43),
    ("C-WTLND", "WETLAND BUFFER 75 FT", 20, 40),
    ("C-WTLND", "WETLAND BUFFER SETBACK", 22, 37),
    ("C-EROS2", "SILT FENCE LIMIT", 25, 30),
    ("C-NOTES", "REV 3 2026-06-20 PER TOWN COMMENTS", 10, 20),
]


def build() -> None:
    doc = ezdxf.new("R2010")
    for name in LAYERS:
        if name not in doc.layers:
            doc.layers.add(name)

    msp = doc.modelspace()
    for layer, text, x, y in TEXTS:
        msp.add_text(
            text,
            dxfattribs={"layer": layer, "height": 1.0, "insert": (x, y)},
        )

    if "TITLEBLOCK_FRAME" not in doc.blocks:
        block = doc.blocks.new(name="TITLEBLOCK_FRAME")
        block.add_lwpolyline(
            [(0, 0), (40, 0), (40, 12), (0, 12), (0, 0)],
            dxfattribs={"layer": "TITLEBLOCK"},
        )
        block.add_text(
            "BROOKSIDE MEADOWS TITLEBLOCK",
            dxfattribs={"layer": "TITLEBLOCK", "height": 1.0},
        )
    msp.add_blockref(
        "TITLEBLOCK_FRAME", (5, 85), dxfattribs={"layer": "TITLEBLOCK"}
    )

    msp.add_line((30, 60), (35, 58), dxfattribs={"layer": "C-STORM"})
    msp.add_lwpolyline(
        [(48, 53), (56, 53), (56, 58), (48, 58), (48, 53)],
        dxfattribs={"layer": "C-STORM"},
    )
    msp.add_line((20, 40), (40, 40), dxfattribs={"layer": "C-WTLND"})
    msp.add_line((25, 29), (45, 29), dxfattribs={"layer": "C-EROS2"})

    msp.add_text(
        "MISC ANNOTATION",
        dxfattribs={"layer": "V-MISC", "height": 1.0, "insert": (80, 15)},
    )
    msp.add_line((80, 14), (90, 14), dxfattribs={"layer": "V-MISC"})

    doc.saveas(OUTPUT)


if __name__ == "__main__":
    build()
    print(f"wrote {OUTPUT}")
