"""Generate the synthetic Brookside Meadows sample DXF fixture.

This script writes a small, safe-to-parse DXF file used by the Phase 11 CAD
intake demo and tests. The drawing is synthetic review-support seed data. It is
not a real survey or engineering drawing and contains no georeferenced
coordinates.

The fixture intentionally includes:

* titleblock-like text
* several civil-style layers
* plan sheet references (one matching a seeded sheet, one intentionally missing)
* a clear detail reference and an intentionally ambiguous one
* pipe labels
* basin labels with an intentional possible conflict
* outfall and wetland buffer text
* a revision note

Run with: python -m app.cad_samples.generate_sample
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

OUTPUT = Path(__file__).resolve().parent / "brookside_meadows.dxf"

# Civil-style layers. Most map to a review category; V-MISC is intentionally
# uncategorized so the parser must flag it for human review.
LAYERS = [
    "C-STORM",
    "C-GRAD",
    "C-EROS",
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
    ("C-NOTES", "SEE SHEET C-9.9 FOR OFFSITE DRAINAGE", 10, 77),
    ("C-NOTES", "DETAIL 3/C-5.1 TYPICAL TRENCH SECTION", 10, 74),
    ("C-NOTES", "SEE DETAIL ?/C-5.X FOR HEADWALL", 10, 71),
    ("C-STORM", "P-12", 30, 60),
    ("C-STORM", "P-7", 35, 58),
    ("C-STORM", "WET BASIN A", 50, 55),
    ("C-STORM", "BASIN A", 52, 52),
    ("C-STORM", "DETENTION BASIN 1", 60, 50),
    ("C-STORM", "OUTFALL 1", 70, 45),
    ("C-STORM", "OF-1", 72, 43),
    ("C-WTLND", "WETLAND BUFFER 75 FT", 20, 40),
    ("C-WTLND", "WETLAND BUFFER SETBACK", 22, 37),
    ("C-NOTES", "REV 2 2026-05-01 PER TOWN COMMENTS", 10, 20),
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

    # A titleblock block definition with one insert, so block extraction has
    # something to report.
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

    # A few plain geometry entities on civil layers.
    msp.add_line((30, 60), (35, 58), dxfattribs={"layer": "C-STORM"})
    msp.add_lwpolyline(
        [(48, 53), (56, 53), (56, 58), (48, 58), (48, 53)],
        dxfattribs={"layer": "C-STORM"},
    )
    msp.add_line((20, 40), (40, 40), dxfattribs={"layer": "C-WTLND"})

    # An uncategorized civil-style layer with content, so the parser must flag
    # it for human review rather than silently guessing a category.
    msp.add_text(
        "MISC ANNOTATION",
        dxfattribs={"layer": "V-MISC", "height": 1.0, "insert": (80, 15)},
    )
    msp.add_line((80, 14), (90, 14), dxfattribs={"layer": "V-MISC"})

    doc.saveas(OUTPUT)


if __name__ == "__main__":
    build()
    print(f"wrote {OUTPUT}")
