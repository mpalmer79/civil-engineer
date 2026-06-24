# CAD Integration Roadmap

This document describes a staged path for CAD integration in Civil Engineer AI.
It is a plan, not a statement of current capability. As of Phase 7, no Autodesk
integration exists, and the system does not parse PDF, DWG, or DXF files, verify
CAD drawings, or perform final design review. The CAD-aware metadata and the
plan sheet viewer hotspots are seeded and synthetic.

Civil Engineer AI is a review-support and evidence-organization system at every
stage below. None of these stages changes that boundary: the system organizes
plan sheet and CAD-aware evidence for a human reviewer and never approves plans,
certifies compliance, or replaces a Professional Engineer.

## Stage 1: Phase 6, seeded plan sheet and CAD-aware metadata (implemented)

- Plan sheet index with sheet metadata, revisions, and missing sheet detection.
- CAD-aware civil feature metadata, seeded rather than extracted.
- Plan references connecting documents, sheets, and features.
- Plan consistency findings that require human review.

This stage establishes the data model and review workflow that later stages
build on.

## Stage 2: Phase 7, plan sheet viewer and sheet hotspot annotations (implemented)

- A reviewer-facing plan sheet viewer with a synthetic sheet preview.
- Seeded hotspot annotations tied to plan consistency findings and civil feature
  references, placed with percentage coordinates over the preview.
- A reviewer can open a sheet, inspect the connected references, CAD-aware
  metadata, documents, checklist items, and plan consistency findings in place,
  and record review-support actions on plan consistency findings.

This stage is a viewing and annotation layer. It renders a synthetic preview
with seeded hotspots and does not parse real PDF, DWG, DXF, or Autodesk data and
does not extract CAD geometry. Real sheet rendering from submitted PDFs is
deferred to a later stage. See `PHASE_7_PLAN_SHEET_VIEWER.md`.

## Stage 3: Phase 8, DXF metadata extraction or structured plan exports

- Read structured metadata from DXF files or structured plan exports.
- Populate the existing `cad_metadata` records with a `future_cad_extraction`
  source type rather than a new schema.
- Compare extracted feature labels against the seeded and document references.

This stage begins reading real CAD-derived metadata, still as review-support
evidence, not as a verified or certified drawing.

## Stage 4: Phase 9, Autodesk Platform Services viewer exploration

- Explore Autodesk Platform Services for viewing and deriving metadata from CAD
  models.
- Evaluate authentication, file translation, and viewer integration as a
  research effort.

This stage is exploratory. It does not imply that Autodesk integration is
production ready, and any work here remains review-support only.

## Stage 5: Phase 10, CAD and document cross-reference automation

- Automate the cross-reference between CAD-derived metadata and document
  evidence.
- Surface plan consistency findings from extracted data with the same human
  review and audit guarantees as today.

Even fully automated, cross-reference findings remain review-support findings
that need reviewer confirmation. The system does not make final engineering
decisions at any stage.
