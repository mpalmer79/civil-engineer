# Phase 6: Plan Sheet and CAD-Aware Review Foundation

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

Phase 6 begins the transition from document-only review into plan sheet and
CAD-aware review support. It adds the first plan sheet intelligence layer for
Civil Engineer AI without attempting full CAD parsing.

Civil Engineer AI remains a review-support and evidence-organization system. It
does not approve plans, certify compliance, stamp or seal drawings, replace a
Professional Engineer, verify CAD drawings, or make final engineering decisions.

## What Phase 6 adds

- A plan sheet data model and a seeded Brookside Meadows plan sheet index.
- A CAD-aware metadata model with seeded civil feature records (basins, pipes,
  roads, lots, utilities, and more).
- A plan reference model that connects documents, sheets, and civil features.
- Missing sheet detection for sheets that are referenced but not included.
- A plan consistency check that generates review-support findings from the
  seeded references and sheets.
- API endpoints for plan sheets, CAD metadata, plan references, and plan
  consistency findings.
- A Plan Sheets page and a CAD-Aware Review page in the frontend.
- Audit events for every step of the plan consistency check.
- Backend tests for sheet indexing, missing sheet detection, CAD metadata
  filtering, reference consistency, the consistency check, audit events, and the
  safety language boundary.

## Why plan sheets matter in civil review

In land development, the plan set is the center of review. A reviewer reads the
narrative and reports, then turns to the plan sheets to confirm that what the
documents describe is actually drawn, labeled, and revised consistently. A
missing referenced sheet, a basin labeled two different ways, or an unclear
revision can each stall a review. Modeling the plan sheet index lets Civil
Engineer AI connect document findings to the sheets a reviewer would open next.

## Why CAD-aware metadata is useful before real CAD parsing

Real CAD parsing (DWG or DXF extraction, Autodesk Platform Services, GIS, OCR,
or computer vision plan reading) is a large effort with its own data and
infrastructure requirements. Before any of that, a structured CAD-aware metadata
layer is valuable on its own:

- It gives the system a vocabulary of civil features (basin, pipe, culvert,
  catch basin, outfall, road, lot, utility, easement, wetland buffer,
  construction entrance, erosion control) that future CAD extraction can fill.
- It lets the system reason about which sheet, layer, and discipline a feature
  belongs to.
- It connects features to documents, checklist items, and findings today, so
  the review workflow already understands plan sheets.
- It provides a future-ready abstraction: when CAD extraction arrives, it
  populates the same metadata records rather than a new schema.

The Phase 6 metadata is seeded and synthetic. It is labeled `seeded_metadata`,
`sheet_index`, `plan_note`, or `report_reference`, with `future_cad_extraction`
reserved for later phases. Nothing in Phase 6 verifies a drawing as correct.

## How the plan sheet index works

The `plan_sheets` table records each sheet with a number, title, discipline,
revision, revision date, status, file name, and purpose, plus related documents,
checklist items, and findings. The seeded Brookside Meadows plan set has twelve
sheets:

| Sheet | Title | Discipline | Status |
| --- | --- | --- | --- |
| C-0.0 | Cover Sheet | cover | present |
| C-1.0 | Existing Conditions Plan | existing_conditions | present |
| C-2.0 | Subdivision Layout Plan | layout | present |
| C-3.0 | Grading and Drainage Plan | grading | present |
| C-3.1 | Revised Grading and Drainage Plan | grading | referenced_not_included |
| C-4.0 | Utility Plan | utility | present |
| C-5.0 | Erosion and Sediment Control Plan | erosion_control | present |
| C-5.1 | Construction Phasing and Erosion Control Details | erosion_control | needs_reviewer_confirmation |
| C-6.0 | Stormwater Management Details | details | present |
| C-7.0 | Roadway Profiles | profiles | present |
| C-8.0 | Landscape and Buffer Plan | landscaping | present |
| D-1.0 | Construction Details | details | present |

Sheet C-3.1 is intentionally referenced but not included so the missing sheet
detection has concrete work to surface. The plan sheet summary reports the total
sheet count, present sheets, missing or referenced-not-included sheets, sheets
with related findings, and the CAD-aware metadata record count.

## How CAD metadata is modeled

The `cad_metadata` table records each civil feature with an entity type, label,
layer name, discipline, source type, and the sheet, document, checklist item, or
finding it relates to. Sixteen features are seeded for Brookside Meadows,
including Basin A and Basin 1 (the conflicting basin labels), the meadow
infiltration basin, the wet detention basin, Brookside Drive, Meadow Court, the
Quarry Road culvert, Outfall 1, Pipe P-12, Catch basin CB-7, the wetland buffer,
the construction entrance, silt fence, the utility pump station, and Lots 17 and
33.

## How plan references connect documents, sheets, and civil features

The `plan_references` table records where the package points from one place to
another and the seeded evaluation outcome (`consistent`, `missing_target`,
`conflicting_label`, `unclear`, or `needs_human_review`). The references connect,
for example, the stormwater report to sheet C-3.0, the stormwater report to the
missing sheet C-3.1, the drainage calculations to Basin A, the O&M plan to the
wet detention basin, the inspection note to Outfall 1, the RFI log to Pipe P-12,
and the erosion control plan to Sheet C-5.1.

## How consistency findings are created

The plan consistency service evaluates every plan reference and the plan sheet
index. References whose status is anything other than `consistent` generate a
plan consistency finding:

- `missing_target` to a sheet becomes `missing_referenced_sheet`.
- `missing_target` to a feature becomes `missing_plan_reference`.
- `conflicting_label` becomes `conflicting_label`.
- `unclear` becomes `unclear_revision`.
- `needs_human_review` becomes `requires_human_review`.

Each finding links the related sheets, documents, CAD metadata, and checklist
items derived from the reference, and every finding is created with the status
`requires_human_review`. The check is idempotent: it removes and regenerates the
findings on each run. It writes audit events for the start, the sheet index
load, the CAD metadata load, each reference evaluated, each finding created, and
completion. The six seeded inconsistencies produce six plan consistency
findings.

## How this prepares for future Autodesk or CAD integration

The CAD-aware metadata model is the seam for future CAD work. A future DXF or
Autodesk extraction step can populate the same `cad_metadata` records with a
`future_cad_extraction` source type, and the same plan reference and consistency
machinery will continue to work. See
[`docs/CAD_INTEGRATION_ROADMAP.md`](CAD_INTEGRATION_ROADMAP.md) for the staged
path.

## What remains out of scope

Phase 6 does not add real DWG or DXF parsing, Autodesk Platform Services live
integration, CAD automation, GIS integration, OCR, computer vision plan reading,
real client files, authentication, deployment work, vector search, semantic
embeddings, final design review, automated approval, or professional
certification.

## What Phase 7 should build next

Phase 7 should add a plan sheet PDF viewer with sheet hotspot annotations, so a
reviewer can open a sheet and see the plan consistency findings and civil
feature references in place. It should also consider persisting human review
actions on plan consistency findings, consistent with the Phase 5 human review
workflow.
