# Phase 0: Foundational Civil Engineering and Product Blueprint

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Repository:** `civil-engineer`
**Phase:** 0, Foundation (documentation and blueprint only; no application code)
**Status:** Draft for review

---

## 0. How to Read This Document

This is the anchor document for the project. It defines what Civil Engineer AI
is, why it starts with stormwater review, how it is intended to grow, and the
professional boundaries that constrain every part of the design.

The companion Phase 0 documents extend this brief:

| Document | Purpose |
| --- | --- |
| `PHASE_0_FOUNDATION.md` | This file. The story, boundaries, and v1 thesis. |
| `BROOKSIDE_MEADOWS_PROJECT_STORY.md` | The realistic fictional development used as the demo and seed data. |
| `DOMAIN_MODEL.md` | The core entities, fields, relationships, and ER diagram. |
| `V1_SCOPE.md` | What the first build includes, excludes, and must prove. |
| `ROADMAP.md` | The staged path from documentation to a multi-module platform. |
| `SEED_DATA_PLAN.md` | Seed-ready project, document, checklist, finding, and evaluation data. |

The existing `RESEARCH_AND_SYSTEM_DESIGN.md` and `ARCHITECTURE.md` remain the
source of truth for the research basis, checklist logic, and system
architecture. This document does not replace them; it frames them and sets the
product direction for the larger platform.

> **Naming note.** The canonical product name is **Civil Engineer AI**, the full
> title is **Civil Engineer AI: Stormwater Review Assistant**, and the canonical
> demo project is **Brookside Meadows**. These names are used consistently across
> the documentation and the codebase.

---

## 1. What Civil Engineer AI Is

Civil Engineer AI is a **review-support and evidence-organization system for
land development workflows.**

It helps a human reviewer, a municipal engineer, a staff civil engineer, or a
consulting reviewer, work through a stormwater and site-plan submission
package faster and with better traceability. It does this by:

- Organizing the submitted document package into searchable, source-linked
  evidence.
- Comparing the package against a structured stormwater review checklist.
- Surfacing where evidence appears **present, missing, unclear, or
  conflicting**.
- Drafting reviewer-facing follow-up language for a human to accept, edit, or
  reject.
- Recording an audit trail of what the system retrieved, what the AI generated,
  and what the human decided.
- Measuring its own accuracy against a library of evaluation cases.

The defining design idea is that the AI model is **one constrained component
inside a controlled review workflow**, not the product itself. The product is
the workflow: retrieval, checklist structure, source citation, human review,
auditability, and evaluation. A reviewer should always be able to ask, "Where
did this come from, and who decided it?" and get a clear answer.

### What Civil Engineer AI Is *Not*

Civil Engineer AI is **not** a system that designs or approves civil
engineering plans. It is not a substitute for licensed engineering judgment,
and it is not marketed or framed as one. See Section 4.

---

## 2. Why Stormwater Review Is the First Module

Stormwater and site-plan review is the right first module for six reasons:

1. **It is document-heavy and checklist-driven.** Real stormwater review is
   already organized around completeness checks, design-storm assumptions, BMP
   evidence, soils, and O&M responsibility. That structure maps cleanly onto a
   retrieval + checklist + findings architecture.

2. **The failure modes are concrete and detectable.** Missing infiltration
   testing, mismatched design storms, an O&M plan with no named maintenance
   owner, an inspection note with no corrective action, these are real,
   recurring review issues that an evidence-organization system can flag
   without making engineering judgments.

3. **The professional boundary is clear and defensible.** Stormwater review
   has a bright line between *organizing evidence and flagging gaps* (safe for
   software) and *certifying that a design is adequate and safe* (licensed work
   only). That clarity makes it an honest portfolio domain.

4. **It is narrow enough to finish.** A single mock project with ~10 to 14
   documents and ~15 checklist items is a completable vertical slice.

5. **It is grounded in authoritative public guidance.** EPA construction and
   post-construction stormwater resources, NRCS soils references, FEMA and FHWA
   drainage guidance, and state/municipal stormwater manuals provide a credible
   research basis (see `RESEARCH_AND_SYSTEM_DESIGN.md`, Section 2, and the
   source list in that document).

6. **It generalizes.** Every primitive built for stormwater, documents,
   chunks, checklist items, findings, risk flags, review actions, audit events,
   evaluation cases, is reusable for grading, utilities, roadway, erosion
   control, permitting, and inspection review. Stormwater is the proving ground
   for a platform, not a one-off demo.

---

## 3. How It Grows Into a Land Development Intelligence Platform

The stormwater module is **module one of a multi-module land development review
platform.** The architecture is deliberately built so that adding a new
review domain means adding *checklist content, document types, and evaluation
cases*, not rebuilding the engine.

The long-term platform is intended to support the full lifecycle of a
neighborhood development project:

1. Stormwater management review *(v1 module)*
2. Drainage calculations and report evidence review
3. Grading and earthwork review
4. Roadway layout review
5. Utility coordination review
6. Erosion and sediment control review
7. Permitting checklist review
8. Construction phasing review
9. Inspection note tracking
10. RFI and submittal follow-up
11. Neighborhood development timeline tracking
12. Municipal comment-response tracking
13. Human review and audit logging *(cross-cutting from day one)*
14. Evaluation of AI-generated findings *(cross-cutting from day one)*

The reusable backbone that makes this expansion cheap:

- **A document/chunk/retrieval layer** that does not care whether a document is
  a drainage report or a utility plan.
- **A checklist engine** where each module contributes its own checklist items
  with the same schema.
- **A findings + risk-flag model** that is domain-agnostic.
- **A human-review queue and audit log** shared by every module.
- **An evaluation harness** that every module plugs expected findings into.

The story chosen for v1, **Brookside Meadows**, a residential subdivision, 
deliberately includes grading, roadway, utility, erosion-control, phasing, and
inspection content even though v1 only *reviews* the stormwater slice. That way
the same seed project carries the platform vision forward without new data
work. See `BROOKSIDE_MEADOWS_PROJECT_STORY.md`.

---

## 4. Professional Boundaries That Govern the Project

This is a portfolio GenAI system. It must never present itself as a licensed
engineering tool. These boundaries are not a disclaimer bolted on at the end, 
they shape the prompts, the database status values, the UI labels, the audit
records, and the evaluation tests.

### 4.1 Civil Engineer AI Must Not

- Approve engineering plans
- Certify compliance
- Stamp or seal drawings
- Replace a licensed Professional Engineer
- Make final public safety determinations
- Claim that a design is safe
- Claim that a project is compliant without human confirmation
- Perform final drainage, grading, roadway, or utility design decisions

### 4.2 Civil Engineer AI May

- Organize evidence
- Summarize documents
- Identify missing information
- Flag inconsistencies
- Compare documents against checklist items
- Draft reviewer follow-up comments
- Route findings to human review
- Maintain audit history
- Support evaluation cases
- Help a reviewer understand what may need attention

### 4.3 Sanctioned Language

Use:

- *Potential issue*
- *Requires reviewer confirmation*
- *Missing evidence*
- *Conflicting information*
- *Based on uploaded documents*
- *Recommended follow-up*
- *Needs human review*
- *Review-support finding*

Avoid:

- *Approved*
- *Certified*
- *Fully compliant*
- *Safe*
- *Engineer-confirmed*
- *Passes review*
- *Meets all requirements*

### 4.4 Why the Boundary Matters

Stormwater review affects flooding risk, water quality, public infrastructure,
and long-term maintenance liability. Professional engineering ethics, the NSPE
and ASCE codes, place public health, safety, and welfare at the center of
practice, and reserve design adequacy and safety determinations for licensed
judgment. A portfolio system earns more credibility by respecting that line
than by pretending to cross it. The boundary is enforced in code through:

- **Status vocabulary** that omits `approved` / `compliant`
  (`supported`, `missing`, `conflicting`, `unclear`, `not_applicable`,
  `requires_human_review`).
- **Prohibited-wording checks** in AI output validation.
- **A required human review action** before any finding is treated as resolved.

---

## 5. What a Human Reviewer Must Always Control

The human reviewer is the authority. The system is the assistant. The following
decisions are reserved for the human and can never be made final by the AI:

- Whether drainage or hydraulic calculations are technically correct.
- Whether a proposed stormwater practice is properly designed and sized.
- Whether a design satisfies local, state, or federal requirements.
- Whether public safety is protected.
- Whether a plan should be approved, conditioned, or denied.
- Whether a drawing or report should be stamped or sealed.
- Whether a corrective action or substitute design is adequate.
- Whether a finding is valid, how it should be worded, and whether it is sent
  to the applicant.

Concretely, every AI-generated finding lands in a **human review queue** in a
`requires_human_review` (or `pending`) state. The reviewer may **accept, edit,
reject, escalate, mark unclear, or request more information**. Both the AI
output and the human decision are recorded in the audit log.

---

## 6. What the AI System May Safely Assist With

Within the boundary above, the AI layer is genuinely useful for:

- Summarizing uploaded project documents with source links.
- Extracting candidate values (design storm names, BMP types, basin IDs,
  outfall labels, maintenance owner references, RFI status) for human
  confirmation.
- Comparing retrieved evidence against a specific checklist item and proposing
  a status (`supported` / `missing` / `conflicting` / `unclear`).
- Drafting reviewer-facing follow-up comments and RFI language.
- Summarizing the set of open, unresolved issues across the package.

Every one of these outputs is **draft, source-cited, and human-reviewable.**
When retrieval finds no useful evidence, the system marks the item `missing` or
`unclear` rather than inventing an answer.

---

## 7. What the V1 System Should Prove

V1 is a single end-to-end vertical slice over the Brookside Meadows stormwater
package. It is successful if it proves the following claims about the builder
and the system:

1. **The system reasons over real submitted evidence, not memory.** Findings
   cite specific documents, pages, and chunks.
2. **Structure drives the review.** A checklist engine, not an open-ended
   prompt, decides what gets examined.
3. **Gaps and conflicts are detected, not just summaries produced.** The system
   catches the intentionally planted issues in the Brookside Meadows package
   (missing infiltration testing, conflicting design storm, unnamed O&M owner,
   unresolved RFI, etc.).
4. **Humans stay in control.** No finding is final without a recorded human
   action.
5. **Everything is auditable.** A reviewer can trace any finding back through
   retrieval, prompt version, and review decision.
6. **The system measures itself.** Evaluation cases report recall, precision,
   false positives/negatives, and source-citation accuracy against expected
   findings.
7. **The professional boundary holds.** The system never emits prohibited
   wording and never claims approval or compliance.

The concrete v1 success criteria and scope live in `V1_SCOPE.md`.

---

## 8. What "Portfolio Impressive" Means Here

For this project, "impressive" is not a flashy chatbot. It is evidence that the
builder understands how to design a **safe, structured, evaluated GenAI system
in a domain where professional judgment matters.** Specifically:

- **Domain credibility.** The workflow, document types, checklist, and risk
  categories read like they came from someone who has actually reviewed
  subdivision and stormwater packages, not from a generic template.
- **Architecture maturity.** Retrieval-augmented generation, structured JSON
  output with schema validation, prompt versioning, and a clear service
  boundary between checklist, retrieval, AI, review, and audit.
- **Human-in-the-loop discipline.** A real review queue with real actions, not
  a "looks good" button.
- **Auditability.** Every AI action and human decision is traceable.
- **Evaluation-driven development.** A test harness with expected findings,
  recall/precision, and citation-accuracy metrics, the single biggest
  differentiator between a serious system and a demo.
- **Responsible-AI judgment.** Explicit, enforced professional boundaries and
  safe language, demonstrating that the builder knows where automation should
  stop.
- **Product vision.** A narrow, finishable v1 whose architecture makes the
  larger land development platform obvious.

A reviewer or hiring manager should come away thinking: *this person can take a
real professional workflow, model it correctly, wrap an LLM in the right
guardrails, prove it works, and know exactly where the human has to stay in
charge.*

---

## 9. Phase 0 Exit Criteria

Phase 0 is complete when:

- [x] The foundation brief (this document) defines the product, boundaries,
      and v1 thesis.
- [x] The Brookside Meadows project story is detailed enough to become seed
      data.
- [x] The domain model defines every core entity with fields, relationships,
      and an ER diagram.
- [x] V1 scope is explicit about in-scope, out-of-scope, and success criteria.
- [x] The roadmap shows the staged path from documentation to a multi-module
      platform.
- [x] The seed data plan provides seed-ready project, document, checklist,
      finding, and evaluation data.
- [ ] The documents have been reviewed and approved before any code is written.

No application code is written until the last box is checked.
