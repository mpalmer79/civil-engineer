# CAD Integration Roadmap

This document describes a staged path for CAD integration in Civil Engineer AI.
It is a plan, not a statement of current capability. As of Phase 11, the system
parses real DXF files for review-support metadata, but no Autodesk or Civil 3D
integration exists, and the system does not parse DWG or PDF files, run OCR or
GIS, verify CAD drawings, or perform final design review. The seeded plan
sheets, CAD-aware metadata, plan sheet viewer hotspots, review packet, workflow
board, and response package remain synthetic; the Phase 11 DXF extraction reads
a real DXF file but is review-support metadata only.

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

## Stage 3: Phase 11, DXF metadata extraction (implemented)

- Read structured metadata from real DXF files with the ezdxf library: layers,
  entities, blocks, and text.
- Detect sheet, detail, pipe, basin, outfall, and wetland buffer references with
  confidence labels and human-review flags.
- Compare extracted sheet and detail references against the seeded plan sheets
  and raise review-support findings, which can become workflow items.

This stage reads real CAD-derived metadata, still as review-support evidence,
not as a verified or certified drawing. DXF is the only supported file type.
DWG parsing, Autodesk and Civil 3D object intelligence, structured plan exports,
GIS, OCR, and computer vision remain future work in the stages below. See
`PHASE_11_CAD_INTAKE_DXF_PARSING.md`.

## Stage 4: a later phase, DWG support and Autodesk Platform Services exploration

- Add DWG support through appropriate tooling, which usually requires
  proprietary or heavier libraries than DXF parsing.
- Explore Autodesk Platform Services and Civil 3D object intelligence for
  viewing and deriving metadata from CAD models.
- Evaluate authentication, file translation, and viewer integration as a
  research effort.

This stage is exploratory. It does not imply that DWG, Autodesk, or Civil 3D
integration is production ready, and any work here remains review-support only.

## Stage 5: a later phase, CAD and document cross-reference automation

- Automate the cross-reference between CAD-derived metadata and document
  evidence.
- Surface plan consistency findings from extracted data with the same human
  review and audit guarantees as today.

Even fully automated, cross-reference findings remain review-support findings
that need reviewer confirmation. The system does not make final engineering
decisions at any stage.
