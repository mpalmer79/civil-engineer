# Phase 6: Plan Sheet and CAD-Aware Review Foundation

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Demo fixture:** Brookside Meadows

Phase 5 added persisted human review actions and evaluation scoring. Phase 6
begins the transition from document-only review into plan sheet and CAD-aware
review support. It does not parse CAD files. It builds a professional foundation
that shows how civil plan sheets, drawing references, CAD-derived metadata,
stormwater reports, checklist items, review findings, and human review actions
connect.

Civil Engineer AI remains a review-support and evidence-organization system. It
does not approve plans, certify compliance, stamp drawings, replace a
Professional Engineer, verify CAD drawings, or make final engineering decisions.

## What Phase 6 adds

- A plan sheet data model and a seeded Brookside Meadows plan sheet index.
- A CAD-aware metadata model for civil features (basins, pipes, roads, lots,
  utilities, and more).
- Plan references that connect documents, sheets, and civil features.
- Missing sheet detection (for example the referenced but not included revised
  grading sheet C-3.1).
- A plan consistency check that generates review-support findings.
- API endpoints for plan sheets, CAD metadata, plan references, and plan
  consistency findings.
- A Plan Sheets page and a CAD-Aware Review page in the frontend.
- A Phase 6 panel on the Evaluation page.
- Documentation of the future Autodesk and CAD integration path.

## Why plan sheets matter in civil review

Civil land development review is sheet-centric. A reviewer reads a plan set: the
cover sheet and index, existing conditions, layout, grading and drainage,
utilities, erosion control, details, and profiles. Findings, comments, and
follow-up requests are almost always tied to specific sheets. A document-only
view misses the structure that reviewers actually work in. Modeling the plan
sheet index makes the review support far closer to real practice.

## Why CAD-aware metadata is useful before real CAD parsing

Real CAD parsing (DWG or DXF) is heavy and is intentionally out of scope here.
But the value of CAD data in review is mostly in the feature-level metadata:
what basins, pipes, roads, lots, and utilities exist, on which sheets, on which
layers, and how they are labeled. By modeling that metadata now as a seeded,
future-ready abstraction, Civil Engineer AI can demonstrate cross-references and
consistency checks today and populate the same shape from a DXF export or an
Autodesk viewer later, without changing the review logic.

## How the plan sheet index works

The `plan_sheets` table records one row per sheet with a sheet number, title,
discipline, revision, revision date, status, file name, purpose, and links to
related documents, checklist items, and findings. Statuses include current,
present, superseded, needs_reviewer_confirmation, missing, and
referenced_not_included. There is no approved status. The plan sheet summary
reports total sheets, present sheets, missing or referenced-not-included sheets,
sheets with related findings, and CAD-aware metadata record counts.

## How CAD metadata is modeled

The `cad_metadata` table records one row per civil feature reference with an
entity type (basin, pipe, culvert, catch_basin, outfall, road, lot, utility,
easement, wetland_buffer, construction_entrance, erosion_control,
sheet_reference), an entity label, a layer name, a discipline, a source type
(seeded_metadata, sheet_index, plan_note, report_reference,
future_cad_extraction), and links to a sheet, document, checklist item, and
finding. This is seeded metadata, not extracted CAD geometry.

## How plan references connect documents, sheets, and civil features

The `plan_references` table records a reference from a source (document, plan
sheet, or civil feature) to a target, with a reference label, context, a
consistency status (consistent, missing_target, conflicting_label, unclear,
needs_human_review), and a review note. For example, the stormwater report
references grading sheet C-3.0 (consistent) and the revised sheet C-3.1
(missing_target), and the drainage calculations reference Basin A while the
report references Basin 1 (conflicting_label).

## How consistency findings are created

The plan consistency service reads the seeded sheets, CAD metadata, and
references and generates review-support findings with simple, explainable rules:

1. Each sheet with status missing or referenced_not_included becomes a
   missing_referenced_sheet finding.
2. A basin labeled both Basin A and Basin 1 across the plan set and report
   becomes a conflicting_label finding.
3. Each remaining inconsistent plan reference becomes one finding, mapped by its
   consistency status to a missing_plan_reference, unclear_revision,
   cad_metadata_gap, or requires_human_review finding.

The check is idempotent: it clears and regenerates the project's plan
consistency findings, updates nothing destructive elsewhere, and writes audit
events. Every finding is created with status requires_human_review. The
generated finding types are missing_referenced_sheet, conflicting_label,
missing_plan_reference, cad_metadata_gap, unclear_revision, and
requires_human_review. No finding uses final-decision language.

For Brookside Meadows the check produces six findings:

1. Referenced revised grading sheet C-3.1 is not included.
2. Basin naming conflict between Basin A and Basin 1.
3. RFI references Pipe P-12 but the pipe material response is missing.
4. Inspection note references Outfall 1 but the corrective action is not shown
   on a current plan sheet.
5. O&M plan references wet detention basin maintenance but ownership notes are
   unclear.
6. Erosion control phasing references Sheet C-5.1 but construction sequence
   notes are incomplete or unclear.

## Review and evaluation integration

Plan consistency findings link to related checklist items and, through the
shared finding ids, to the existing AI draft findings and expected findings
where relevant (for example the C-3.1 missing sheet, the basin naming conflict,
the open RFI on Pipe P-12, and the inspection corrective action). They use safe
status values, require human review, and are included in the Evaluation page
summary metrics. Full human review action persistence for plan findings (the
accept, edit, reject lifecycle from Phase 5) is documented as Phase 7 work and
is not forced into this phase.

## Audit events

The plan consistency check writes: plan_consistency_check_started,
plan_sheet_index_loaded, cad_metadata_loaded, plan_reference_evaluated (one per
reference), plan_consistency_finding_created (one per finding),
plan_consistency_check_completed, and plan_consistency_check_failed on error.
Metadata includes the project id, sheet id, cad metadata id, reference id, plan
finding id, consistency status, related entity labels, and count summaries. No
secrets are logged.

## How this prepares for future Autodesk or CAD integration

The CAD-aware metadata model is the seam for later CAD work. The source_type
field already anticipates a future_cad_extraction source, and the entity model
matches what a DXF export or an Autodesk Platform Services viewer would supply.
See `CAD_INTEGRATION_ROADMAP.md` for the staged path. None of that integration
exists yet.

## What remains out of scope

Phase 6 does not add real DWG or DXF parsing, Autodesk Platform Services
integration, CAD automation, GIS integration, OCR, computer vision plan reading,
real client files, authentication, deployment work, vector search, semantic
embeddings, final design review, automated approval, or professional
certification.

## What Phase 7 should build next

Phase 7 should add a plan sheet PDF viewer and sheet hotspot annotations, and
extend the Phase 5 human review action lifecycle to plan consistency findings so
a reviewer can accept, edit, reject, escalate, mark unclear, or request more
information on each plan finding with persisted actions and audit events.
