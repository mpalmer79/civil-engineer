# Phase 7: Plan Sheet Viewer and Sheet Hotspot Review

Phase 7 adds a reviewer-facing plan sheet viewer on top of the Phase 6 plan
sheet and CAD-aware foundation. A reviewer can open a Brookside Meadows plan
sheet, see seeded visual hotspot annotations over a synthetic sheet preview,
inspect the connected plan references, CAD-aware metadata, documents, checklist
items, and plan consistency findings, and record review-support actions on plan
consistency findings.

Civil Engineer AI remains a review-support and evidence-organization system. It
does not approve plans, certify compliance, stamp or seal drawings, replace a
Professional Engineer, verify CAD drawings, validate final design, or make final
engineering decisions.

## What Phase 7 adds

- A plan sheet hotspot model (`plan_sheet_hotspots`) with percentage coordinates
  and links back to Phase 6 plan references, CAD metadata, plan consistency
  findings, documents, and checklist items.
- A plan consistency review action model (`plan_consistency_review_actions`) so a
  reviewer can record a decision on a plan consistency finding.
- A sheet viewer context endpoint that bundles a sheet with its hotspots and the
  related evidence.
- Backend services, schemas, endpoints, and seed data for the above.
- A reviewer-facing Sheet Viewer in the frontend with a synthetic plan sheet
  preview, a hotspot overlay, and detail and review panels.
- Audit events for viewer context requests, hotspot inspection, plan review
  actions, and seeded hotspot loading.
- Backend tests for the hotspots, the viewer context, and the review actions.

## Why a seeded viewer, not real PDF or CAD parsing

Phase 7 deliberately does not parse real PDF, DWG, DXF, or Autodesk data. Real
plan rendering and CAD extraction are large efforts with their own data and
infrastructure requirements (see `CAD_INTEGRATION_ROADMAP.md`). The value a
reviewer gets first is spatial context: seeing where a finding sits on a sheet
and what it connects to. A synthetic preview with seeded hotspot coordinates
delivers that experience now, on top of the Phase 6 data, while staying honest
that the preview and hotspots are seeded review-support metadata. When real
sheet rendering or CAD extraction arrives later, the same hotspot and viewer
model can be populated from real sources without changing the review workflow.

## Sheet hotspot model

Each `plan_sheet_hotspots` record carries:

- `hotspot_id`, `project_id`, `sheet_id`
- `hotspot_type`, `label`, `description`
- `x_percent`, `y_percent`, `width_percent`, `height_percent`
- `severity` (low, medium, high)
- `related_plan_reference_ids`, `related_cad_metadata_ids`,
  `related_plan_finding_ids`, `related_document_ids`,
  `related_checklist_item_ids`
- `review_note`, `requires_human_review`, `created_at`

Coordinates are percentages of the synthetic sheet preview, so the overlay
scales with the preview. Hotspot types are descriptive review-support
categories: missing referenced sheet, basin label conflict, maintenance
ownership, pipe reference, unclear revision, erosion control detail, basin
outlet detail, and wetland buffer setback. No type or severity uses
final-decision language.

The seeded Brookside Meadows fixture includes eight hotspots across six sheets,
each tied back to a Phase 6 entity where possible:

1. C-3.0, missing referenced sheet (revised grading sheet C-3.1 not included).
2. C-3.0, basin label conflict (Basin A versus Basin 1).
3. C-3.0, maintenance ownership (wet detention basin ownership unclear).
4. C-4.0, pipe reference (Pipe P-12 material response missing).
5. C-6.0, basin outlet detail (Outfall 1 corrective action not shown).
6. C-5.1, unclear revision (construction sequence notes unclear).
7. C-5.0, erosion control detail (construction entrance and silt fence).
8. C-8.0, wetland buffer setback (buffer near the outfall).

## Plan consistency review actions

A reviewer can record one of four actions on a plan consistency finding:

- `needs_follow_up`
- `reviewer_confirmed`
- `not_applicable`
- `needs_more_information`

There is intentionally no action called approve. Each action maps to a finding
status of the same name, records the previous and new status, requires a
reviewer note, and rejects any note that contains prohibited final-decision
wording. Every action keeps the finding a review-support finding under human
control and writes audit events.

## Sheet viewer context

`GET /api/v1/plan-sheets/{sheet_id}/viewer-context` returns the sheet, its
hotspots, the CAD-aware metadata on the sheet, the plan references that touch the
sheet (directly or through a feature on it), the plan consistency findings
related to the sheet, and a preview note stating that the preview and hotspots
are seeded review-support metadata. Requesting the context writes a
`sheet_viewer_context_requested` audit event.

## API endpoints

- `GET /api/v1/projects/{project_id}/sheet-hotspots`
- `GET /api/v1/projects/{project_id}/sheet-hotspots/summary`
- `GET /api/v1/plan-sheets/{sheet_id}/sheet-hotspots`
- `GET /api/v1/plan-sheets/{sheet_id}/viewer-context`
- `GET /api/v1/sheet-hotspots/{hotspot_id}`
- `POST /api/v1/plan-consistency-findings/{plan_finding_id}/review-actions`
- `GET /api/v1/plan-consistency-findings/{plan_finding_id}/review-actions`
- `GET /api/v1/projects/{project_id}/plan-consistency-review-actions`

## Frontend

The Sheet Viewer is reachable from the primary navigation. The `/sheet-viewer`
page lists the plan sheets and highlights those with seeded hotspots. The
`/sheet-viewer/{sheetId}` page renders the `PlanSheetViewer`, which composes:

- `SheetHotspotOverlay`: numbered annotation regions over the preview.
- `SheetHotspotPanel`: details for the selected hotspot.
- `SheetReferencePanel`: connected plan references, CAD metadata, documents, and
  checklist items.
- `PlanFindingReviewPanel`: the related plan consistency findings and a reviewer
  action form.

Phase 7 data is backend-canonical. When the backend is unavailable the viewer
shows a helpful message and never simulates hotspots or review actions in the
browser.

## Audit events

- `sheet_hotspot_review_data_seeded` (when the seeded hotspots are loaded)
- `sheet_viewer_context_requested` (when a viewer context is requested)
- `sheet_hotspot_inspected` (when a single hotspot is opened)
- `plan_consistency_review_action_recorded` (when a review action is recorded)
- `plan_finding_status_updated` (when a review action changes a finding status)

## What remains out of scope

Phase 7 does not add real PDF, DWG, DXF, or Autodesk parsing, CAD automation,
GIS integration, OCR, computer vision plan reading, real client files,
authentication, deployment work, vector search, semantic embeddings, final
design review, automated approval, or professional certification. The sheet
preview is synthetic and the hotspots are seeded review-support annotations.

## What Phase 8 should build next

Phase 8 begins reading real CAD-derived metadata: DXF metadata extraction or
structured plan exports that populate the existing `cad_metadata` records with a
`future_cad_extraction` source type, compared against the seeded and document
references. Real sheet rendering and Autodesk Platform Services exploration
remain later stages in `CAD_INTEGRATION_ROADMAP.md`. Every finding stays a
review-support finding that requires human review.
