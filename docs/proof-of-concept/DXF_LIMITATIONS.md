# DXF Proof Limitations

Stated plainly, the proof of concept does not prove:

* correct basin sizing
* correct pipe slope
* adequate hydraulic capacity
* correct grading
* regulatory compliance
* construction readiness
* design safety
* final plan approval
* survey accuracy
* complete CAD semantic understanding

Those determinations belong to a licensed Professional Engineer and were not
attempted.

## Technical limitations

* Reference matching runs against the seeded Brookside Meadows plan-sheet
  index. A project without an index cannot distinguish a missing sheet from
  an unindexed one.
* Paper-space entities are inventoried in the parse audit metadata, not
  persisted per entity. Per-entity space tagging is future work.
* Geometry bounds for splines, ellipses, hatches, and dimensions are safe
  overestimates, not exact envelopes. Entities with no safe bound report an
  explicit reason and never fabricated coordinates.
* Construction lines (XLINE, RAY) are unbounded by definition and report as
  unsupported for bounds.
* Layer classification is a routing aid. A layer named C-STORM routes to the
  stormwater queue; nothing checks that its content is correct or complete.
  The PROP token is mapped to property lines at medium confidence and is
  documented as ambiguous (some firms use it for proposed work).
* A possible facility naming inconsistency is a reviewer question, never a
  confirmed design conflict.
* One generated drawing plus the generated corpus is proof of functionality,
  not broad compatibility with every drafting convention. Expanding the
  corpus is on the roadmap.
* Parse safety limits: entities beyond 100,000 are counted but not persisted
  individually (recorded as a parse warning finding), text values are
  truncated at 2,000 characters, and layer persistence caps at 5,000.
  Partial parsing is allowed and always visible.
* DXF is the only supported CAD format. DWG parsing, Autodesk integration,
  OCR, and GIS remain intentionally out of scope.
