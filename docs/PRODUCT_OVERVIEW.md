# Product Overview

Civil Engineer AI is a review-support platform for stormwater plan review. This overview describes the product by workflow and capability. It is the place to start for understanding what the product does and how a reviewer uses it.

Civil Engineer AI organizes review-support evidence for a human reviewer. It does not approve plans, certify compliance, verify CAD, validate engineering design, or make final engineering decisions. A licensed Professional Engineer remains responsible for any final decision.

## Who it is for

A municipal reviewer, a civil engineering reviewer, an internal QA reviewer, or a project manager who needs to organize a stormwater submission, track findings across review rounds, and prepare communication back to an applicant, while keeping every step traceable and under human control.

## The review workflow

### 1. Intake

A reviewer uploads a DXF file through the browser. The system validates the file by extension, size, content type, and readability, stores it under a safe generated file name that prevents path traversal, and registers it for review. DXF is the only supported file type.

### 2. CAD metadata parsing

The backend parses the DXF file with the ezdxf library and extracts review-support metadata: layers, entities, blocks, text, and reference candidates such as sheet references, detail references, and pipe, basin, outfall, and wetland buffer labels. Each reference candidate carries a confidence label and a human-review flag. The parser compares extracted references against the plan sheet index and raises review-support findings for missing matches, unclear details, possible label conflicts, and uncategorized layers. This is metadata extraction only; it does not verify CAD or validate geometry.

### 3. Evidence and findings

Findings link back to their source evidence with document and page references. A reviewer can see the role each piece of evidence plays (supports, missing, conflict, or context) and confirm or act on each finding. Every finding stays under human review.

### 4. Review packet

A reviewer assembles documents, checklist items, findings, plan sheets, CAD-aware metadata, hotspots, plan consistency findings, human review actions, and audit evidence into a structured review packet draft. An evidence traceability matrix shows the links row by row, and a printable review-support summary is available.

### 5. Workflow board

A reviewer promotes packet items into an operational workflow board. Items move through triage, follow-up, more information requests, reviewer checked, and ready for handoff. Every status transition, reviewer note, and follow-up request is recorded and audited. Ready for handoff means the organized evidence is ready to hand to a licensed Professional Engineer.

### 6. Response package

A reviewer turns ready-for-handoff items into a structured draft external response package for an applicant, design engineer, municipal reviewer, or internal review team. The package groups items by topic, drafts plain review-support wording, keeps traceability to the workflow item and source evidence, and adds an attachment checklist, a printable draft, a package history, and a human review sign-off checklist. The system never sends the response itself.

### 7. Resubmittal and revision comparison

When an applicant returns a resubmittal, a reviewer records it, links the revised DXF file and applicant response notes, and runs a revision comparison against the previous DXF parse round. The comparison uses extracted DXF metadata only and surfaces added, removed, changed, unchanged, and carried-forward references. The reviewer maps applicant responses to prior items, marks review-support resolution statuses, carries unresolved items forward without duplication, and prepares the next round.

### 8. Reviewer command center

The Project Dashboard aggregates the whole review state into one operational view: project health metrics, reviewer attention items with recommended next steps, a project timeline, review readiness checks, reviewer notes, and links into every module. It answers what needs attention now, what changed since the last round, what is carried forward, what is ready for handoff, where evidence is incomplete, and what to do next. It links into the existing modules rather than replacing them.

## Capability summary

| Capability | What it does |
| --- | --- |
| Reviewer Command Center | Aggregates attention items, health metrics, a timeline, readiness checks, and next steps. |
| Browser DXF Upload | Validates and safely stores an uploaded DXF file. |
| CAD Intake and Metadata Parsing | Extracts layers, references, blocks, and text from a real DXF file. |
| Plan Sheet Viewer | Opens a plan sheet with seeded hotspot annotations. |
| Review Packet Builder | Assembles evidence into a structured packet draft. |
| Workflow Board | Tracks items from triage to handoff. |
| Response Package Builder | Drafts an external response with an attachment checklist and sign-off. |
| Resubmittal and Revision Comparison | Compares DXF metadata across review rounds. |
| Evidence Traceability | Links findings to source evidence. |
| Audit Trail | Records reviewer actions and accesses. |

## Status language

Every status in the product is a review-support status. The product uses words such as needs review, needs follow-up, needs more information, reviewer checked, carried forward, addressed for review, ready for handoff, and ready for human review. It never uses final-decision language such as approved, certified, verified, compliant, safe, resolved, or closed, and there is no action named approve.

## Technical foundation

The frontend is a Next.js application with a typed TypeScript API client. The backend is a FastAPI application with a clear service layer per capability, SQLAlchemy models on SQLite, and a central safety vocabulary that enforces the professional boundary at the data layer. DXF parsing uses the ezdxf library. Live AI calls are disabled by default. The backend and frontend deploy as two separate Railway services; see the Railway deployment guide for details.
