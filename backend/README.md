# Civil Engineer AI Backend

FastAPI backend for Civil Engineer AI: Stormwater Review Assistant. This is the
Phase 11 backend. It serves seeded Brookside Meadows review data, document
chunks, and source evidence, runs a controlled AI review workflow that produces
draft review-support findings, persists human review actions on those drafts,
scores AI review runs against the expected findings, adds a plan sheet and
CAD-aware review foundation (a plan sheet index, CAD-aware feature metadata, plan
references, missing sheet detection, and plan consistency findings), adds a
plan sheet viewer layer (seeded sheet hotspots, a sheet viewer context, and
human review actions on plan consistency findings), adds a review packet
builder (a review-support packet draft with sections, items, evidence links, an
evidence traceability matrix, and a printable summary), adds a reviewer
workflow board (workflow items promoted from the packet, with status
transitions, reviewer notes, follow-up requests, and a ready-for-handoff
summary), adds an external review response package (ready-for-handoff workflow
items turned into a draft external response grouped by topic, with draft
wording, an attachment checklist, a printable draft, a package history, and a
human review sign-off checklist), and adds real CAD intake for DXF files (parsed
with ezdxf into layers, entities, blocks, text, reference candidates, and
review-support findings, compared against the seeded plan sheets).

Civil Engineer AI is a review-support and evidence-organization system. It does
not send email, approve plans, certify compliance, stamp drawings, or replace a
licensed Professional Engineer. Statuses, retrieval results, AI draft findings,
human review actions, plan consistency findings, sheet hotspots, review packet
items, workflow items, response items, and CAD review findings never use
final-decision language, there is no action called approve, and every finding
requires human review. The seeded CAD-aware metadata, sheet hotspots, review
packet, workflow board, and response package remain synthetic. Phase 11 parses
real DXF files for review-support metadata only; it does not verify CAD, validate
the design, or parse DWG, PDF, GIS, or run OCR.

The AI Review Assistant uses a deterministic mock provider by default, so the
backend runs without any API key. Only an OpenAI live provider is implemented,
and live provider calls are disabled by default. Phase 11 parses DXF files with
ezdxf (a lightweight pure-Python library) but does not include embeddings, a
vector store, DWG or PDF parsing, Autodesk or GIS integration, OCR, computer
vision, authentication, or email sending.

## Requirements

- Python 3.11 or newer

## Setup

From the `backend` directory:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional, defaults work without it
```

## Seed the database

The database is also seeded automatically on first startup if it is empty. To
seed (or reset and reseed) explicitly:

```bash
python -m app.db.seed
```

This loads the Brookside Meadows fixture: 19 documents, 19 checklist items, 10
findings, 10 audit events, 8 evaluation cases, 10 hotspots, 56 document chunks,
and 21 finding sources. To seed (or reset and reseed) the Phase 6 plan sheet and
CAD-aware data explicitly:

```bash
python -m app.db.seed_plansheets
```

This loads 12 plan sheets, 16 CAD-aware metadata records, and 11 plan
references, generates the plan consistency findings, and seeds 8 plan sheet
hotspots for the Phase 7 viewer.

## Start the backend

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs are at
`http://localhost:8000/docs`.

## Run tests

```bash
pytest
```

Tests use an isolated temporary SQLite database and never touch the development
database.

## Health endpoint

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"Civil Engineer AI Backend","phase":"8"}
```

## API route examples

All data routes are under the `/api/v1` prefix. The seeded project id is
`proj_brookside_meadows`.

```bash
# Projects
curl http://localhost:8000/api/v1/projects
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows

# Documents
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/documents
curl http://localhost:8000/api/v1/documents/doc_stormwater_report

# Checklist
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/checklist
curl http://localhost:8000/api/v1/checklist/chk_infiltration_testing

# Findings
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/findings
curl http://localhost:8000/api/v1/findings/find_infiltration_missing

# Audit events
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/audit-events

# Evaluation cases
curl http://localhost:8000/api/v1/evaluation-cases
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/evaluation-cases

# Hotspots
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/hotspots

# Document chunks
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/chunks
curl http://localhost:8000/api/v1/documents/doc_stormwater_report/chunks
curl http://localhost:8000/api/v1/chunks/chunk_swm_001

# Retrieval and source evidence
curl "http://localhost:8000/api/v1/projects/proj_brookside_meadows/search?query=infiltration%20testing"
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/checklist/chk_infiltration_testing/evidence
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/findings/find_infiltration_missing/evidence
curl http://localhost:8000/api/v1/findings/find_infiltration_missing/sources

# AI Review Assistant (mock provider by default)
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/ai-provider-mode
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/ai-review-runs
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/draft-findings

# Human review queue and review actions (Phase 5)
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/human-review-queue
curl -X POST http://localhost:8000/api/v1/draft-findings/DRAFT_ID/review-actions \
  -H "Content-Type: application/json" \
  -d '{"action":"accepted","reviewer_name":"Town Engineer","reviewer_note":"Evidence inspected."}'
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/review-actions

# Evaluation scoring (Phase 5)
curl -X POST http://localhost:8000/api/v1/ai-review-runs/REVIEW_RUN_ID/evaluate
curl http://localhost:8000/api/v1/ai-review-runs/REVIEW_RUN_ID/evaluation
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/ai-evaluation-results

# Plan sheets and CAD-aware review (Phase 6)
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-sheets
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-sheets/summary
curl http://localhost:8000/api/v1/plan-sheets/sheet_c31
curl "http://localhost:8000/api/v1/projects/proj_brookside_meadows/cad-metadata?entity_type=basin"
curl http://localhost:8000/api/v1/plan-sheets/sheet_c40/cad-metadata
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-references
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-references/inconsistencies
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-consistency-check
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-consistency-findings

# Plan sheet viewer and sheet hotspots (Phase 7)
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/sheet-hotspots
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/sheet-hotspots/summary
curl http://localhost:8000/api/v1/plan-sheets/sheet_c30/sheet-hotspots
curl http://localhost:8000/api/v1/plan-sheets/sheet_c30/viewer-context
curl http://localhost:8000/api/v1/sheet-hotspots/hs_c30_basin_conflict
curl -X POST http://localhost:8000/api/v1/plan-consistency-findings/plan_find_pref_calcs_basin_a/review-actions \
  -H "Content-Type: application/json" \
  -d '{"action":"needs_follow_up","reviewer_name":"Town Engineer","reviewer_note":"Confirm basin label."}'
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/plan-consistency-review-actions

# Review packet builder (Phase 8)
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/review-packets/generate
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/review-packets
curl http://localhost:8000/api/v1/review-packets/PACKET_ID
curl http://localhost:8000/api/v1/review-packets/PACKET_ID/summary
curl http://localhost:8000/api/v1/review-packets/PACKET_ID/traceability
curl http://localhost:8000/api/v1/review-packets/PACKET_ID/print-view
curl -X POST http://localhost:8000/api/v1/review-packets/PACKET_ID/items/ITEM_ID/review-actions \
  -H "Content-Type: application/json" \
  -d '{"action_type":"reviewer_checked","reviewer_name":"Town Engineer","reviewer_note":"Checked."}'
curl -X PATCH http://localhost:8000/api/v1/review-packets/PACKET_ID/items/ITEM_ID/status \
  -H "Content-Type: application/json" \
  -d '{"new_status":"needs_follow_up","reviewer_note":"Follow up needed."}'

# Reviewer workflow board (Phase 9)
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-board/generate
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-board
curl "http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-board?status=needs_follow_up"
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-board/summary
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-board/ready-for-handoff
curl http://localhost:8000/api/v1/workflow-items/WORKFLOW_ITEM_ID
curl http://localhost:8000/api/v1/workflow-items/WORKFLOW_ITEM_ID/history
curl -X PATCH http://localhost:8000/api/v1/workflow-items/WORKFLOW_ITEM_ID/status \
  -H "Content-Type: application/json" \
  -d '{"new_status":"needs_triage","reviewer_name":"Town Engineer","reviewer_note":"Starting triage."}'
curl -X POST http://localhost:8000/api/v1/workflow-items/WORKFLOW_ITEM_ID/notes \
  -H "Content-Type: application/json" \
  -d '{"reviewer_name":"Town Engineer","reviewer_note":"Reviewer needs to check the basin outlet detail."}'
curl -X POST http://localhost:8000/api/v1/workflow-items/WORKFLOW_ITEM_ID/follow-ups \
  -H "Content-Type: application/json" \
  -d '{"requested_from":"Applicant","request_reason":"Need the updated drainage report.","requested_information":"Revised drainage report.","reviewer_name":"Town Engineer"}'

# External review response package (Phase 10)
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/response-packages/generate
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/response-packages
curl http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID
curl http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/summary
curl http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/attachments
curl http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/print-view
curl http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/history
curl -X PATCH http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/status \
  -H "Content-Type: application/json" \
  -d '{"new_status":"reviewer_checked","reviewer_name":"Town Engineer","reviewer_note":"Looks reasonable."}'
curl -X PATCH http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/items/RESPONSE_ITEM_ID/status \
  -H "Content-Type: application/json" \
  -d '{"new_status":"included","reviewer_name":"Town Engineer"}'
curl -X PATCH http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/items/RESPONSE_ITEM_ID/draft-text \
  -H "Content-Type: application/json" \
  -d '{"draft_text":"Please provide the revised drainage report for review.","reviewer_name":"Town Engineer"}'
curl -X POST http://localhost:8000/api/v1/response-packages/RESPONSE_PACKAGE_ID/items/RESPONSE_ITEM_ID/notes \
  -H "Content-Type: application/json" \
  -d '{"reviewer_name":"Town Engineer","reviewer_note":"Discuss with the applicant first."}'

# Real CAD (DXF) intake (Phase 11)
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/cad-files \
  -H "Content-Type: application/json" \
  -d '{"sample_key":"brookside_meadows","uploaded_by":"Town Engineer"}'
curl -X POST http://localhost:8000/api/v1/cad-files/CAD_FILE_ID/parse
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/cad-files
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/cad-parse-runs
curl http://localhost:8000/api/v1/cad-parse-runs/PARSE_RUN_ID/summary
curl http://localhost:8000/api/v1/cad-parse-runs/PARSE_RUN_ID/layers
curl http://localhost:8000/api/v1/cad-parse-runs/PARSE_RUN_ID/text
curl http://localhost:8000/api/v1/cad-parse-runs/PARSE_RUN_ID/reference-candidates
curl -X POST http://localhost:8000/api/v1/cad-parse-runs/PARSE_RUN_ID/compare-plan-sheets
curl http://localhost:8000/api/v1/projects/proj_brookside_meadows/cad-review-findings
curl -X POST http://localhost:8000/api/v1/projects/proj_brookside_meadows/workflow-items/from-cad-findings
curl http://localhost:8000/api/v1/cad-files/CAD_FILE_ID/review-context
```

The `GET /review-packets/{packet_id}`, `/traceability`, and `/print-view`
endpoints write an audit event recording reviewer access. The workflow item
detail, item history, board summary, and ready-for-handoff endpoints do the
same, as do the response package detail, print view, attachments, and history
endpoints, and the CAD parse summary, layers, text, and CAD file review context
endpoints. This read side effect is intentional so the decision history shows
reviewer access.

DXF is the only supported CAD file type. For this phase, intake uses the bundled
Brookside Meadows sample DXF resolved by sample_key, so no arbitrary path is read
from the client. Browser DXF upload is a later enhancement. DWG parsing is out of
scope.

## AI provider configuration

The AI Review Assistant defaults to a deterministic mock provider. No API key is
required and live calls are disabled by default. Configure with environment
variables (see `.env.example`):

```env
AI_PROVIDER=mock
AI_MODEL=mock-review-v1
AI_ENABLE_LIVE_CALLS=false
OPENAI_API_KEY=
PROMPT_VERSION=checklist_review_v1
```

Only the OpenAI live provider is implemented today. To enable it: set
`AI_PROVIDER=openai`,
`AI_ENABLE_LIVE_CALLS=true`, provide `OPENAI_API_KEY` (never commit it), set
`AI_MODEL`, and install the optional package with `pip install openai`. If the
live provider is unavailable, the service falls back to the mock provider.

## Project layout

```text
backend/
  app/
    main.py            FastAPI app, health endpoint, CORS, startup seeding
    core/
      config.py        Environment driven settings
      safety.py        Allowed status vocabulary and prohibited wording rules
    db/
      database.py      Engine, session factory, declarative base
      models.py        SQLAlchemy models
      seed.py          Canonical Brookside Meadows seed data and loader
      seed_evidence.py Seeded chunks, finding sources, retrieval queries
      seed_plansheets.py Seeded plan sheets, CAD metadata, references, and hotspots
    schemas/           Pydantic response schemas
    services/          Service layer including the review packet builder, workflow board, response package, and CAD intake
    cad_samples/       Bundled sample DXF fixture and its generator
    api/
      routes.py        Aggregate v1 router
      v1/              One module per resource
  tests/               pytest suite
```

## Data source of truth

For Phase 2 the Python seed data in `app/db/seed.py` is the canonical runtime
source. The frontend TypeScript data under the repository `data` folder is kept
as a graceful fallback used only when the backend cannot be reached. The two are
aligned and describe the same Brookside Meadows fixture.
