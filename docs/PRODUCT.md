# Product

This is the canonical product overview for Civil Engineer AI. It describes what
the product does, who it is for, the review workflow, the capability boundary,
and the honest map of what is real versus seeded. It folds in the former
product-overview, SaaS-positioning, metrics-boundary, and real-vs-mocked
documents.

Civil Engineer AI is a review-support platform for stormwater plan review. It
organizes review-support evidence for a human reviewer. It does not approve
plans, certify compliance, verify CAD, validate engineering design, or make final
engineering decisions. A licensed Professional Engineer remains responsible for
any final decision.

## Who it is for

A municipal reviewer, a civil engineering reviewer, an internal QA reviewer, or a
project manager who needs to organize a stormwater submission, track findings
across review rounds, and prepare communication back to an applicant, while
keeping every step traceable and under human control. Small to mid-sized civil
and AEC firms running internal pre-submittal QA are the primary audience;
municipal review departments are a secondary, later audience.

The core value is organization and traceability: documents indexed to the page
level, findings linked to their evidence, checklist status at a glance, applicant
responses recorded across rounds, and a reviewer-controlled handoff package. It
reduces clerical burden so the engineer's time goes to judgment. It is review
support, not review automation: nothing here sizes a basin, checks a code
section, or approves anything.

## The review workflow

1. Intake: a reviewer uploads a DXF file through the browser. The system
   validates it by extension, size, content type, and readability, and stores it
   under a safe generated file name that prevents path traversal.
2. CAD metadata parsing: the backend parses the DXF with the ezdxf library and
   extracts layers, entities, blocks, text, and reference candidates. This is
   metadata extraction only; it does not verify CAD or validate geometry.
3. Evidence and findings: findings link back to source evidence with document and
   page references, and each stays under human review.
4. Review packet: a reviewer assembles documents, checklist items, findings, plan
   sheets, CAD-aware metadata, and audit evidence into a structured packet draft
   with an evidence traceability matrix.
5. Workflow board: packet items move through triage, follow-up, more-information
   requests, reviewer checked, and ready for handoff, with every transition
   audited. Ready for handoff means organized evidence is ready to hand to a
   licensed Professional Engineer.
6. Response package: ready-for-handoff items become a structured draft response
   package with plain review-support wording, an attachment checklist, and a human
   sign-off checklist. The system never sends the response itself.
7. Resubmittal and revision comparison: when an applicant returns a resubmittal,
   a reviewer records it, links the revised DXF and response notes, and runs a
   revision comparison against the previous DXF parse round using extracted
   metadata only.
8. Reviewer command center: the Project Dashboard aggregates the whole review
   state into one operational view and links into the modules rather than
   replacing them.

## Status language

Every status in the product is a review-support status: needs review, needs
follow-up, needs more information, reviewer checked, carried forward, addressed
for review, ready for handoff, and ready for human review. It never uses
final-decision language such as approved, certified, verified, compliant, safe,
resolved, or closed, and there is no action named approve.

## Capability boundary

This is the canonical, code-checked statement of what is and is not implemented.
Use this wording in public copy so positioning does not drift.

- Real DXF parsing: yes. The backend parses DXF files with ezdxf and extracts
  layers, entities, blocks, text, and reference candidates. This is metadata
  extraction, not geometry validation or compliance certification.
- Real PDF indexing: yes, text-layer only. pypdf extracts embedded page text
  where it exists. There is no OCR, so scanned-image pages are not read; they are
  recorded as having no extractable text.
- OCR: not included.
- DWG parsing: not supported. Uploads are limited to the .dxf extension.
- GIS integration and georeferencing: not supported. DXF bounds are treated as
  local drawing coordinates.
- Computer vision and vector search: not included.
- Live AI calls: disabled by default. The default provider is a deterministic
  mock; live calls require an explicit provider, an enable flag, and a key.
- Seeded Brookside Meadows records are labeled as seeded review-support data and
  are not presented as extracted from a real submission. The bundled sample DXF is
  the exception that is actually parsed, and its CAD findings come from that parse.

The product does not approve plans, certify compliance, stamp drawings, verify,
validate, or make final engineering decisions. It does not guarantee compliance,
declare a project safe, or promise passing review.

## Real versus seeded

Status labels: Implemented (a real code path), Seeded demo (synthetic fixture
data exercising a real UI, clearly labeled), Simulated (a deterministic stand-in
for a future capability, honest about being illustrative), Static prototype
(fixed values chosen for presentation stability), Planned (named in the roadmap,
not built), and Out of scope (deliberately excluded).

| Area | Status |
| --- | --- |
| Brookside Meadows project data | Seeded demo |
| Homepage case-study facts | Seeded demo |
| Reviewer queue and access control | Implemented |
| Document review and PDF page indexing | Implemented plus seeded demo library |
| Evidence citations (pypdf, deterministic retrieval) | Implemented |
| DXF metadata parsing (ezdxf) | Implemented |
| Plan sheets and hotspots | Seeded demo |
| Applicant response packages and resubmittals | Implemented |
| Audit trail | Implemented plus seeded demo events |
| AI guidance and assistant behavior | Simulated, live AI disabled by default |
| Authentication and roles | Implemented, local |
| DWG, Autodesk, Civil 3D, GIS, OCR, computer vision | Out of scope |
| Deployment (two Railway services, CI) | Implemented |

None of these rows, individually or together, make this a licensed engineering
review system. Every output is review-support material for a human decision
maker. The public demo runs on the seeded Brookside Meadows fixture; authenticated
surfaces never substitute seeded data after a failure, they render explicit error
states instead. See `docs/REFERENCE_PROJECT.md` for the reference project and
`docs/ROADMAP.md` for planned work.
