# CivilSite AI: Stormwater Review Assistant

CivilSite AI is a portfolio GenAI system that assists stormwater and site-plan review using retrieval-augmented generation, checklist validation, risk flagging, human review, audit logging, and evaluation tracking.

This project is built as a realistic software engineering portfolio project. It is not a licensed civil engineering tool and does not replace professional engineering judgment.

---

## Project Overview

CivilSite AI is designed to support a mock stormwater/site-plan review workflow. The system helps organize project documents, retrieve source evidence, compare submissions against review checklist items, flag potential risks, and route findings to a human reviewer.

The project focuses on one practical use case:

> A stormwater review assistant for a mock commercial redevelopment project.

The system is intentionally designed as a production-style GenAI workflow instead of a basic chatbot. It combines structured data, source-linked retrieval, AI-generated findings, reviewer approval steps, and evaluation metrics.

---

## What This Project Demonstrates

This project is meant to demonstrate applied GenAI engineering skills, including:

* Retrieval-augmented generation over project documents
* Structured document ingestion and chunking
* Checklist-driven review logic
* AI-assisted issue flagging
* Human-in-the-loop review
* Audit logging
* Evaluation tracking
* Safety boundaries for professional workflows
* Backend and frontend system design

The goal is to show how a GenAI system can assist a technical review process while keeping final decisions with a qualified human reviewer.

---

## Important Safety Boundary

CivilSite AI does **not**:

* Approve engineering plans
* Certify compliance
* Stamp or seal drawings
* Replace a licensed Professional Engineer
* Make final public safety determinations
* Claim that a design is safe
* Claim that a project is compliant without human confirmation

The system only supports review by identifying possible missing evidence, conflicting information, unclear documentation, and recommended follow-up items.

CivilSite AI should use language such as:

* Potential issue
* Requires reviewer confirmation
* Missing evidence
* Conflicting information
* Based on uploaded documents
* Recommended follow-up

---

## Core Features

Planned v1 features include:

* Mock stormwater project dashboard
* Document library for review package files
* PDF/text ingestion pipeline
* Document chunking and embedding storage
* Source-linked retrieval
* Stormwater checklist engine
* AI-generated review findings
* Risk flagging
* Human review queue
* Reviewer actions such as accept, edit, reject, escalate, or request more information
* Audit log for traceability
* Evaluation dashboard for measuring system performance

---

## V1 Scope

The first version focuses on one complete vertical slice:

**Mock commercial redevelopment stormwater review**

The system will review a synthetic project package containing sample documents such as:

* Site plan narrative
* Drainage report
* Stormwater calculations
* Soil or geotechnical report
* Infiltration testing notes
* Erosion and sediment control plan
* Operation and maintenance plan
* Inspection notes
* RFI log
* Permit checklist

The v1 system should detect expected issues such as:

* Missing drainage calculations
* Mismatched storm event assumptions
* Missing infiltration testing
* Missing soil or groundwater information
* Unclear outfall information
* Missing operation and maintenance responsibility
* Unresolved RFIs
* Inspection notes without corrective action

---

## Planned Architecture

CivilSite AI is planned as a full-stack GenAI application.

### Frontend

* Next.js
* TypeScript
* Project dashboard
* Document library
* AI review workspace
* Human review queue
* Audit log
* Evaluation dashboard

### Backend

* FastAPI
* Python
* Document ingestion
* Retrieval service
* Checklist engine
* AI review assistant
* Risk flagging service
* Human review workflow
* Audit logger
* Evaluation service

### Database

* PostgreSQL
* pgvector
* Structured project tables
* Document chunk storage
* Embedding search
* Findings and review actions
* Audit events
* Evaluation results

### AI Layer

* OpenAI or Claude API
* Retrieval-augmented generation
* Structured JSON outputs
* Source-linked findings
* Safety wording validation
* Human review requirement

---

## System Workflow

```text
1. A mock stormwater project is created.
2. Review documents are uploaded or seeded.
3. The backend extracts and chunks document text.
4. Embeddings are generated and stored.
5. The checklist engine determines applicable review items.
6. The retrieval service finds source evidence for each checklist item.
7. The AI review assistant generates structured findings.
8. Findings are routed to a human review queue.
9. The reviewer accepts, edits, rejects, escalates, or requests more information.
10. The system records all actions in the audit log.
11. Evaluation cases compare system findings against expected results.
```

---

## Repository Structure

```text
civil-engineer/
├── README.md
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── RESEARCH_AND_SYSTEM_DESIGN.md
│   ├── SAFETY_BOUNDARIES.md
│   ├── EVALUATION_PLAN.md
│   └── SAMPLE_PROJECT_PACKAGE.md
├── frontend/
│   └── README.md
├── backend/
│   └── README.md
├── data/
│   ├── mock-projects/
│   ├── sample-documents/
│   └── evaluation-cases/
└── screenshots/
```

---

## Documentation

* [Architecture](docs/ARCHITECTURE.md)
* [Research and System Design](docs/RESEARCH_AND_SYSTEM_DESIGN.md)
* [Safety Boundaries](docs/SAFETY_BOUNDARIES.md)
* [Evaluation Plan](docs/EVALUATION_PLAN.md)
* [Sample Project Package](docs/SAMPLE_PROJECT_PACKAGE.md)

---

## Evaluation Goals

CivilSite AI will be evaluated on whether it can:

* Detect expected checklist issues
* Cite the correct source documents
* Avoid unsupported engineering conclusions
* Mark uncertain findings for human review
* Avoid prohibited approval or compliance language
* Produce useful reviewer follow-up language
* Maintain a traceable audit history

Planned evaluation metrics include:

* Checklist recall
* Checklist precision
* Source citation accuracy
* False positives
* False negatives
* Unsupported claim count
* Reviewer approval rate
* Reviewer rejection rate
* Unresolved risk count

---

## Current Status

This project is currently in the planning and architecture phase.

Completed or in progress:

* Repository created
* Initial README drafted
* Architecture document drafted
* Research and system design document drafted
* Safety boundaries planned
* Evaluation plan planned
* Mock project package planned

Next steps:

1. Finalize documentation in the `docs/` folder.
2. Create mock project data.
3. Define checklist seed data.
4. Build the backend ingestion and checklist pipeline.
5. Build the frontend project dashboard.
6. Add retrieval and AI review workflows.
7. Add human review and audit logging.
8. Add evaluation cases and metrics.

---

## Portfolio Purpose

This project is being built to demonstrate applied software engineering and GenAI system design. It is intended to show practical understanding of:

* Domain-focused AI workflows
* Technical document review
* RAG architecture
* AI safety boundaries
* Human-in-the-loop systems
* Auditable AI outputs
* Evaluation-driven development

CivilSite AI is a review-support and evidence-organization system. It assists human reviewers. It does not replace licensed civil engineering judgment.

---

## License

This project is intended for portfolio and educational use.
