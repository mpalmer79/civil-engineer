# CAD Integration Roadmap

**Product:** Civil Engineer AI: Stormwater Review Assistant

This document describes a staged path toward CAD-aware review. It is a plan, not
a statement of current capability. As of Phase 6, Civil Engineer AI does not
parse CAD files, does not process DWG or DXF data, and does not integrate with
Autodesk. The system organizes seeded plan sheet and CAD-aware metadata only.

Civil Engineer AI is a review-support and evidence-organization system. No stage
below changes that boundary. The system will not approve plans, certify
compliance, stamp drawings, verify CAD drawings, validate a design, or replace a
Professional Engineer.

## Stage 1, Phase 6: Seeded plan sheet and CAD-aware metadata (delivered)

- Plan sheet index with sheet numbers, disciplines, revisions, and statuses.
- CAD-aware feature metadata for basins, pipes, roads, lots, and utilities.
- Plan references connecting documents, sheets, and features.
- Plan consistency findings for missing sheets and conflicting labels.
- A future-ready metadata abstraction (the source_type field anticipates a
  future_cad_extraction source).

## Stage 2, Phase 7: Plan sheet PDF viewer and sheet hotspot annotations

- Render submitted plan sheet PDFs in the browser as review evidence.
- Place hotspot annotations on a sheet that link to findings and checklist
  items, reusing the existing hotspot model.
- Extend the Phase 5 human review action lifecycle to plan consistency
  findings.
- Still no CAD parsing: the viewer displays PDFs, not CAD geometry.

## Stage 3, Phase 8: DXF metadata extraction or structured plan exports

- Accept structured plan exports (for example a DXF layer and entity listing or
  a CSV feature schedule) and map them into the existing CAD-aware metadata
  shape.
- Populate the cad_metadata table from a real export rather than seed data,
  using the same model so review logic is unchanged.
- Keep extraction read-only and evidence-oriented. No automated design review.

## Stage 4, Phase 9: Autodesk Platform Services viewer exploration

- Explore the Autodesk Platform Services viewer for displaying converted models
  in the browser.
- Treat any model display as source evidence for a human reviewer.
- Document authentication, cost, and data-handling requirements before any
  integration is built.

## Stage 5, Phase 10: CAD and document cross-reference automation

- Automate cross-references between extracted CAD features and document
  references so that label conflicts and missing references are detected from
  real exports.
- Continue to require human review for every finding.
- Continue to avoid final design decisions and approval language.

## Principles across all stages

- Every CAD-derived item is source evidence for a human reviewer, never a
  conclusion.
- The professional boundary holds: no approval, certification, CAD
  verification, or design validation.
- New stages mostly add data sources and viewers behind the existing
  review-support, human-review, audit, and evaluation backbone.
