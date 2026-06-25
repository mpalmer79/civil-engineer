# CAD Integration Roadmap

This document describes a staged path for CAD integration in Civil Engineer AI.
It is a plan, not a statement of current capability. As of Phase 12, the system
parses real DXF files for review-support metadata and accepts browser DXF uploads
with intake validation and a parse review queue, but no Autodesk or Civil 3D
integration exists, and the system does not parse DWG or PDF files, run OCR or
GIS, verify CAD drawings, or perform final design review. The seeded plan
sheets, CAD-aware metadata, plan sheet viewer hotspots, review packet, workflow
board, and response package remain synthetic; the DXF extraction reads a real
DXF file but is review-support metadata only.

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

## Stage 3b: Phase 12, browser DXF upload and parse review queue (implemented)

- Upload a real DXF file through the browser with intake validation (extension,
  size, content type, and readability) and safe storage under a generated file
  name that prevents path traversal.
- Trigger parsing manually through a parse review queue and a CAD intake
  dashboard, with parse status and parse failure visibility. A queue status of
  failed means a technical parse failure, not an engineering failure.
- Review unpromoted CAD findings and promote selected findings into the workflow
  board without creating duplicate workflow items.

This stage makes the Phase 11 DXF parsing usable by a reviewer. It still extracts
review-support metadata only and does not verify CAD, validate design, approve
plans, or certify compliance. DXF remains the only supported file type; DWG,
Autodesk, Civil 3D, GIS, OCR, and computer vision remain future work below. See
`PHASE_12_BROWSER_CAD_UPLOAD.md`.

## Stage 3c: Phase 13, DXF metadata revision comparison across review rounds (implemented)

- Compare the extracted DXF metadata of two parse rounds: layer names and review
  categories, sheet, detail, pipe, basin, outfall, and wetland buffer references,
  other text references, block names, and CAD review findings.
- Surface added, removed, changed, unchanged, and carried-forward references,
  including a sheet reference that is still missing in both rounds and a new
  reference to a missing sheet.

This is a metadata comparison for review support across review rounds. It does
not parse DWG, run OCR or GIS, use computer vision, compare geometry in a way that
implies engineering validation, verify CAD, or validate design. DWG, Autodesk,
Civil 3D, GIS, OCR, and computer vision remain future work in the stages below.
See `PHASE_13_RESUBMITTAL_REVISION_CYCLE.md`.

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
