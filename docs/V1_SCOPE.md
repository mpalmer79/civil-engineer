# V1 Scope, Civil Engineer AI

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

**Product:** Civil Engineer AI: Stormwater Review Assistant
**V1 thesis:** One complete, end-to-end **Stormwater Review Assistant for
Brookside Meadows**, narrow enough to finish, deep enough to prove the
platform.

> V1 does **not** attempt to build every land development module. It builds one
> vertical slice over a single mock project, with the architecture and seed data
> arranged so the other modules are obvious additions, not rewrites.

---

## 1. The One-Sentence Scope

A reviewer can open the seeded **Brookside Meadows** stormwater package, run an
AI-assisted checklist review, inspect the cited evidence behind each finding,
accept/edit/reject/escalate findings, read a full audit trail, and view
evaluation results showing the system caught the expected issues, all without
the system ever approving, certifying, or claiming the design is safe.

---

## 2. What V1 Includes (Build List)

| # | Capability | Description |
| --- | --- | --- |
| 1 | **Mock project dashboard** | Brookside Meadows status: documents, checklist progress, open findings, high-risk count, recent audit activity. |
| 2 | **Seeded Brookside Meadows project** | The full project record from `SEED_DATA_PLAN.md`. |
| 3 | **Seeded document package** | ~14 to 19 synthetic documents with planted issues. |
| 4 | **Document library** | List of documents with type, status, chunk count, and a source-view. |
| 5 | **Stormwater checklist engine** | 12 to 20 reusable checklist items; applicability from project flags. |
| 6 | **Retrieval-ready document chunks** | Documents chunked with page/section metadata; embeddings for source retrieval. |
| 7 | **AI-assisted finding generation** | Per checklist item: retrieve evidence → structured JSON finding with citations and safety check. |
| 8 | **Human review queue** | Pending findings with accept / edit / reject / escalate / mark-unclear / request-info actions. |
| 9 | **Audit log** | Every retrieval, model call, finding, validation result, and human action. |
| 10 | **Evaluation cases** | 6 to 10 cases comparing actual findings to expected, with recall/precision/citation metrics. |

---

## 3. In Scope (Detailed)

- **Stormwater checklist review.** Run the seeded checklist against the seeded
  package and produce a per-item status.
- **Document evidence retrieval.** Semantic + keyword retrieval over document
  chunks, scoped to the project and filtered by document type and checklist
  category. Weak retrieval results are rejected rather than forced into a
  finding.
- **Missing evidence detection.** Detect when expected evidence (e.g.,
  infiltration testing, downstream culvert analysis, revised sheet C-3.1) is
  absent.
- **Conflicting information detection.** Detect mismatches across documents
  (design storm, basin naming) using extracted candidate values and
  `ProposedImprovement.aliases`.
- **Risk flagging.** Map findings to risk categories and levels for the
  dashboard.
- **Human review actions.** Persist a human decision for every finding;
  reflect it in status and audit history.
- **Audit history.** Full traceability from finding → retrieved chunks → prompt
  version → human decision.
- **Evaluation dashboard / data.** Run evaluation cases and display recall,
  precision, false positives/negatives, source-citation accuracy, and a
  prohibited-wording count.

---

## 4. Out of Scope for V1

These are intentionally excluded to keep v1 finishable. Several are roadmap
items (see `ROADMAP.md`), not permanent exclusions.

- Final engineering calculations (hydrology/hydraulics performed by the system)
- Plan approval, conditioning, or denial
- Professional certification, stamping, or sealing
- CAD/DWG file parsing
- GIS integration and spatial analysis
- Full hydraulic/hydrologic modeling (e.g., SWMM runs)
- Real project document upload from actual clients (synthetic data only)
- Automated permit submission to any authority
- Construction management / scheduling execution
- Real-time sensor or IoT integration
- Multi-tenant accounts, authentication, and role-based access control
- The non-stormwater review modules (grading, roadway, utility, etc.), 
  modeled in the domain but not reviewed in v1

---

## 5. V1 Success Criteria

V1 is successful if a reviewer can complete this loop on Brookside Meadows:

1. **Open** the Brookside Meadows project dashboard.
2. **View** the submitted documents in the document library.
3. **Run or inspect** a stormwater checklist review.
4. **See** AI-drafted findings tied to checklist items.
5. **Inspect** the source evidence (document, page, excerpt) behind each
   finding.
6. **Accept, edit, reject, or escalate** each finding.
7. **View** an audit trail reconstructing how each finding was produced and
   decided.
8. **Run** evaluation cases showing the expected findings were detected.

### 5.1 Acceptance Thresholds (Concrete)

| Check | Target |
| --- | --- |
| Planted issues detected (I-1 … I-10) | ≥ 8 of 10 surfaced as findings with correct status family |
| Source citation on evidence-based findings | 100% have ≥ 1 valid `FindingSource` |
| Prohibited wording in any finding | 0 occurrences |
| Findings finalized without a human action | 0 |
| Evaluation cases runnable and scored | All seeded cases produce a result row |
| False positives on the "clean" control case | 0 invented issues; no approval/compliance claims |

---

## 6. What V1 Deliberately Proves

- The system reasons over **submitted evidence**, not model memory.
- **Structure** (the checklist) drives the review.
- **Gaps and conflicts** are found, not just summaries.
- **Humans stay in control** of every finding.
- **Everything is auditable.**
- **The system measures itself.**
- **The professional boundary holds** in language and status values.

(See `PHASE_0_FOUNDATION.md` Section 7 to 8 for the full rationale.)

---

## 7. Build Order Within V1

V1 follows the documentation-first, vertical-slice sequence. The recommended
internal order (expanded in `ROADMAP.md`, Phases 1 to 5):

1. Static portfolio prototype with seeded data (no AI calls).
2. Backend + database schema + seed data + read APIs.
3. Retrieval layer (chunks, embeddings, source search).
4. AI review assistant (structured prompts, JSON validation, safety checks).
5. Evaluation system (expected findings, metrics, dashboard).

The first milestone is **one complete vertical slice** for a single checklist
item, retrieve, generate, validate, review, audit, evaluate, before fanning
out to the full checklist.
