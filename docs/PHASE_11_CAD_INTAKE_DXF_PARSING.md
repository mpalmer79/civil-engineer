# Phase 11: Real CAD File Intake and DXF Parsing Foundation Report

Phase 11 adds real CAD file intake for DXF files. It parses a real DXF file with
the ezdxf library, extracts review-support metadata, connects that metadata to
the existing plan sheet and review workflows, and raises review-support findings
for a human reviewer.

Civil Engineer AI remains a review-support and evidence-organization system.
Parsing extracts metadata from a real DXF file. It does not verify CAD, validate
geometry, hydraulic calculations, grading, stormwater design, or legal
boundaries, certify compliance, approve plans, or replace a licensed
Professional Engineer. There is no action called approve.

## Supported and rejected file types

- Supported: DXF only.
- Rejected or out of scope: DWG parsing, Autodesk and Civil 3D integration, PDF
  plan parsing, OCR, GIS, computer vision, design validation, and quantity
  takeoff certification. DWG support is documented as future work because it
  usually requires proprietary or heavier tooling.

## Parser dependency

Phase 11 uses ezdxf, a lightweight, permissively licensed, pure-Python DXF
library. It is pinned in `backend/requirements.txt` as `ezdxf==1.4.4`. No paid
SDK, Autodesk API, or proprietary integration is used. ezdxf reads the DXF
document, its layer table, model space entities, blocks, and text.

## What Phase 11 adds

- Eight models: CadFileUpload, CadParseRun, CadLayerExtract, CadEntityExtract,
  CadBlockExtract, CadTextExtract, CadReferenceCandidate, and CadReviewFinding.
- A parsing service that extracts layers, entities, blocks, and text, detects
  reference candidates with confidence labels, compares references against
  seeded plan sheets, and raises review-support findings.
- A function to create workflow items from CAD findings.
- API endpoints, audit events, and backend tests.
- A CAD Intake page and detail page in the frontend with a file list, parse
  summary card, layer table, text extract table, reference candidate panel,
  review finding panel, plan sheet comparison panel, review context panel, and a
  CAD limitations notice.

## How parsing works

`create_cad_file_from_sample(project_id, sample_key)` registers a bundled sample
DXF as a CAD file record (file type dxf). The sample is resolved from a
whitelist, so no arbitrary filesystem path is read from the client. Browser file
upload is a later enhancement; this phase is backend fixture-based DXF parsing
with real extraction.

`parse_dxf_file(cad_file_id)` reads the DXF with ezdxf and extracts:

- layers, with an entity count, text and geometry flags, and a review category
- entities, with type, layer, block name, handle, optional local bounding values,
  and a review category
- blocks, with insert counts, layer names, and contained text
- text and mtext values, normalized, with a detected reference type
- reference candidates: sheet references such as C-3.1, detail references such
  as DETAIL 3/C-5.1, pipe labels such as P-12, basin labels such as WET BASIN A,
  outfall labels such as OF-1, wetland buffer labels, and revision notes

Bounding values are stored only when cheaply available from the source entity
(text insert points, line endpoints, polyline vertices). They are local drawing
coordinates and are not treated as georeferenced.

## Reference matching and findings

Extracted sheet and detail references are compared against the seeded Phase 6
plan sheets by sheet number. The service raises review-support findings:

- `missing_plan_sheet_match`: a referenced sheet (for example C-9.9) has no
  matching seeded plan sheet.
- `unclear_detail_reference`: a detail reference is ambiguous (for example
  DETAIL ?/C-5.X) and needs human review.
- `possible_label_conflict`: multiple basin labels share an identifier (for
  example WET BASIN A and BASIN A).
- `unknown_layer_category`: a layer has entities but no recognized review
  category.
- `parse_warning`: the DXF structural audit reported items to review.

Confidence labels are from the allowed set: high, medium, low, and
needs_human_review. There is intentionally no "verified" label, because matching
is review support, not verification. Every finding is a draft that needs human
review.

`create_workflow_items_from_cad_findings(project_id)` promotes CAD findings into
Phase 9 workflow items. It is idempotent per finding: a finding already linked to
a workflow item is skipped.

## Sample DXF fixture

A small synthetic Brookside Meadows DXF is produced by the
`app/cad_samples/generate_sample.py` script and committed at
`app/cad_samples/brookside_meadows.dxf`. It is review-support seed data, not a
real survey or engineering drawing, and contains no georeferenced coordinates.
It intentionally includes titleblock text, several civil-style layers, plan
sheet references (one matching a seeded sheet and one intentionally missing), a
clear detail reference and an intentionally ambiguous one, pipe, basin, outfall,
and wetland buffer labels with an intentional possible basin label conflict, an
uncategorized layer with content, and a revision note. The backend registers and
parses this fixture once at startup so the read endpoints and frontend have data
without a manual call, and the tests parse it directly.

## Parse failures

If ezdxf cannot read a file, the parse run is recorded with status `failed` and
an error message, and the CAD file upload status becomes `parse_failed`. Note
that `failed` here is an operational parse status describing the parser, not a
final engineering determination about the plan.

## Audit events

Phase 11 writes audit events when a CAD file record is created
(`cad_file_created`), a DXF parse starts (`cad_parse_started`), a parse completes
(`cad_parse_completed`) or fails (`cad_parse_failed`), a parse summary is viewed
(`cad_parse_summary_viewed`), layers are viewed (`cad_layers_viewed`), text is
viewed (`cad_text_viewed`), a reference comparison is run
(`cad_reference_comparison_run`), a review finding is created
(`cad_review_finding_created`), workflow items are created from CAD findings
(`cad_workflow_items_created`), and a CAD file review context is viewed
(`cad_review_context_viewed`).

Intentional read side effects: the GET endpoints for the parse summary, layers,
text, and the CAD file review context each write an audit event recording the
access. This is intentional so the decision history shows reviewer access. The
other list endpoints do not write audit events.

## API endpoints

- `POST /api/v1/projects/{project_id}/cad-files`
- `POST /api/v1/cad-files/{cad_file_id}/parse`
- `GET /api/v1/projects/{project_id}/cad-files`
- `GET /api/v1/projects/{project_id}/cad-parse-runs`
- `GET /api/v1/cad-parse-runs/{parse_run_id}`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/summary`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/layers`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/entities`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/blocks`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/text`
- `GET /api/v1/cad-parse-runs/{parse_run_id}/reference-candidates`
- `POST /api/v1/cad-parse-runs/{parse_run_id}/compare-plan-sheets`
- `GET /api/v1/projects/{project_id}/cad-review-findings`
- `POST /api/v1/projects/{project_id}/workflow-items/from-cad-findings`
- `GET /api/v1/cad-files/{cad_file_id}/review-context`

## What remains out of scope

Phase 11 does not add DWG parsing, Autodesk or Civil 3D integration, PDF plan
parsing, OCR, GIS, computer vision, vector search, authentication, deployment
setup, email sending, external paid APIs, design validation, or automated
engineering decisions. The sample is a synthetic DXF, and parsing extracts
review-support metadata only.

## What a later phase could build next

A later phase could add browser DXF upload with size and content validation,
DWG support through appropriate tooling, structured plan exports, and broader
CAD extraction. These remain a separate, later track described in
`CAD_INTEGRATION_ROADMAP.md`.
