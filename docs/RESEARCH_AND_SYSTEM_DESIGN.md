# Civil Engineer AI: Stormwater Review Assistant

> **Naming note.** The product name is **Civil Engineer AI** and the canonical
> demo fixture is **Brookside Meadows** (see `BROOKSIDE_MEADOWS_PROJECT_STORY.md`).
> Examples in this brief use the Brookside Meadows fixture.

## Research and System Design Brief

Civil Engineer AI is a portfolio GenAI system concept for assisting stormwater and site-plan review. It is designed as a review-support tool that helps organize project documents, retrieve source evidence, compare submissions against checklist expectations, flag potential risks, route findings for human review, and preserve an audit trail.

Civil Engineer AI is not a licensed engineering tool. It must not approve plans, certify compliance, stamp drawings, replace a Professional Engineer, or make final public safety determinations. Its purpose is to demonstrate production-style GenAI architecture in a realistic civil engineering workflow.

## 1. Project Purpose

The project is intended to show that a GenAI system can be designed around a real technical workflow instead of acting as a generic chatbot. The core idea is to support a stormwater or site-plan reviewer by using retrieval-augmented generation, structured checklist logic, human review, and evaluation tracking.

The system should answer questions like:

- What documents were submitted?
- Which checklist items appear supported by the uploaded evidence?
- Which items appear missing, unclear, or conflicting?
- Which findings require human review?
- Which source documents support each finding?
- What follow-up language could a reviewer use?
- What did the AI generate, what evidence did it use, and what did the reviewer decide?

The strongest portfolio signal is not that the system uses an AI model. The strongest signal is that it wraps the model in a controlled workflow with retrieval, validation, review, auditability, and evaluation.

## 2. Authoritative Research Basis

This project should be grounded in public stormwater and professional engineering guidance. The sources below support the system design:

- EPA explains that stormwater from construction sites can carry sediment, debris, chemicals, nutrients, oil and grease, concrete washout, and other pollutants into storm sewer systems and surface waters. EPA also states that construction stormwater permits apply to construction activity disturbing one acre or more, or less than one acre when part of a larger common plan of development that will disturb one acre or more. [EPA Construction Stormwater][epa-construction]
- EPA Construction General Permit resources include SWPPP templates, site inspection report templates, dewatering inspection report templates, corrective action log templates, and guidance for distinguishing routine maintenance from corrective action. [EPA CGP Resources][epa-cgp-resources]
- EPA post-construction BMP guidance notes that development increases paved surfaces, stormwater volume, and pollutants. It also describes MS4 program elements such as post-construction runoff ordinances, structural and non-structural BMP strategies, and long-term operation and maintenance programs. [EPA Post-Construction BMPs][epa-post-construction]
- EPA lists BMP categories relevant to this project, including site planning, infiltration, filtration, retention, detention, inlet controls, inspection, and maintenance. [EPA Post-Construction BMPs][epa-post-construction]
- NSPE describes its Code of Ethics as a foundational framework for engineering practice, including professional responsibilities toward the public, employers, and the profession. [NSPE Code of Ethics][nspe-ethics]
- ASCE's Code of Ethics places public health, safety, and welfare at the center of civil engineering professional conduct. [ASCE Code of Ethics][asce-ethics]

These sources support the main boundary for Civil Engineer AI: the system can assist with organizing and flagging review evidence, but licensed engineering judgment must remain with qualified human professionals.

## 3. Civil Engineering Workflow Being Modeled

Civil Engineer AI models a simplified stormwater/site-plan review workflow for a land development or redevelopment project.

### 3.1 Typical Workflow

A realistic review sequence looks like this:

1. **Applicant prepares the submission package**  
   A developer, civil engineer, or design consultant prepares project plans, stormwater calculations, drainage reports, erosion control information, and supporting documentation.

2. **Submission intake**  
   A municipal reviewer, permitting office, or engineering department receives the plan package and confirms whether required documents were provided.

3. **Completeness review**  
   The reviewer checks whether the package includes the expected plans, reports, forms, checklists, calculations, and supporting studies.

4. **Technical review**  
   A municipal engineer, staff civil engineer, or consulting reviewer evaluates whether the design appears to address the applicable stormwater requirements. This often includes drainage areas, design storm assumptions, runoff calculations, proposed BMPs, erosion controls, outfalls, easements, and operation and maintenance responsibilities.

5. **Comment letter or RFI**  
   If items are missing, unclear, inconsistent, or technically unresolved, the reviewer issues comments or requests for information.

6. **Resubmission**  
   The applicant submits revised plans, updated calculations, written responses, or additional supporting documentation.

7. **Follow-up review**  
   The reviewer compares the revised submission against prior comments and determines whether issues remain open.

8. **Construction and inspection**  
   During construction, inspectors may review erosion and sediment control measures, dewatering practices, stabilization, corrective actions, and installation of stormwater controls.

9. **Closeout and maintenance handoff**  
   As-built information, inspection documentation, ownership, and maintenance responsibilities may be reviewed before closeout.

Civil Engineer AI should focus on steps 2 through 7 for v1. Construction inspection support can be included later as an extension.

### 3.2 Participants

| Participant | Role in Workflow | Civil Engineer AI Relevance |
| --- | --- | --- |
| Developer or applicant | Submits the project package | Provides documents and responses |
| Civil design engineer | Prepares plans, calculations, and technical reports | Source of engineering documents |
| Municipal reviewer | Reviews submission for completeness and technical issues | Primary user for v1 |
| Staff civil engineer | Performs or supports engineering review | Human authority for technical judgment |
| Inspector | Reviews field implementation and corrective actions | Future workflow extension |
| Contractor | Builds project and responds to field issues | May appear in RFIs and inspection logs |
| Project manager | Coordinates timeline, responses, and resubmissions | May track open findings and status |

### 3.3 Decisions That Require Licensed Judgment

Civil Engineer AI can flag evidence issues, but it must not make final engineering decisions. The following require licensed or qualified human judgment:

- Whether drainage calculations are technically correct
- Whether a proposed stormwater management practice is properly designed
- Whether a design satisfies local, state, or federal requirements
- Whether public safety is protected
- Whether a plan should be approved
- Whether a drawing or report should be stamped or sealed
- Whether field conditions are acceptable
- Whether a substitute design or corrective action is adequate

Civil Engineer AI should support those decisions by organizing evidence and surfacing potential problems.

## 4. Document Types

The system should recognize common document types used in stormwater and site-plan review.

| Document Type | Purpose | Key Information | Safe AI Use |
| --- | --- | --- | --- |
| Site plans | Show existing and proposed site layout | Parcels, grading, utilities, drainage structures, impervious areas, BMP locations | Extract references, summarize plan sheets, identify missing sheets or labels |
| Drainage report | Explains stormwater design approach | Existing/proposed drainage areas, design storms, runoff methods, calculations, BMP sizing | Summarize assumptions, locate storm event criteria, flag mismatches |
| Hydrology/hydraulic calculations | Supports runoff and conveyance design | Time of concentration, curve numbers, peak flows, routing, pipe/channel capacity | Extract values and compare against checklist expectations |
| Stormwater management report | Describes permanent controls | BMP selection, water quality volume, treatment approach, detention/retention strategy | Identify proposed practices and required supporting evidence |
| Soil report | Describes soil and subsurface conditions | Soil types, boring logs, groundwater, infiltration feasibility | Identify whether soil and groundwater evidence exists |
| Infiltration testing documentation | Supports infiltration BMP design | Test locations, rates, methods, depth to groundwater, test dates | Flag missing or unclear testing evidence |
| Erosion and sediment control plan | Controls construction-phase sediment and pollutants | Construction entrance, silt fence, inlet protection, stabilization, phasing | Compare presence of details against checklist categories |
| SWPPP | Describes stormwater pollution prevention during construction | Site controls, inspections, maintenance, corrective action procedures | Summarize controls and inspection commitments |
| Operation and maintenance plan | Defines long-term BMP care | Owner, inspection schedule, maintenance tasks, access responsibilities | Flag missing maintenance owner or unclear responsibilities |
| Inspection notes | Record field observations | Date, inspector, observed conditions, deficiencies, corrective actions | Identify unresolved field issues |
| RFI log | Tracks questions and responses | RFI number, question, response, status, impacted documents | Flag unresolved or contradictory RFIs |
| Permit checklist | Defines jurisdiction review requirements | Required forms, plan sheets, reports, calculations, signatures | Drive checklist engine |
| Municipal design standards | Define local requirements | Storm events, BMP criteria, submittal requirements, design details | Retrieval source for reviewer support |
| Construction specifications | Define materials and installation standards | Pipe materials, structures, compaction, erosion controls | Identify inconsistencies with plans or RFIs |

## 5. Review Checklist and Risk Categories

The v1 checklist should be narrow, practical, and seed-data friendly. It should focus on review support rather than final compliance.

### 5.1 V1 Checklist

| ID | Category | Review Question | Expected Evidence | Document Types | Risk |
| --- | --- | --- | --- | --- | --- |
| CHK-001 | Completeness | Does the package include a drainage or stormwater report? | Drainage report or stormwater report | Drainage report, stormwater report | High |
| CHK-002 | Design storm | Are design storm assumptions stated? | Storm event names, recurrence intervals, rainfall depths | Drainage report, calculations, municipal standard | High |
| CHK-003 | Consistency | Do storm event assumptions match across documents? | Same event criteria in report and calculations | Drainage report, calculations | High |
| CHK-004 | Drainage areas | Are existing and proposed drainage areas identified? | Drainage area maps or tables | Site plans, drainage report | Medium |
| CHK-005 | Runoff calculations | Are runoff calculations included for existing and proposed conditions? | Peak flow or volume calculations | Calculations, drainage report | High |
| CHK-006 | BMP identification | Are proposed stormwater BMPs identified? | BMP type, location, and purpose | Site plans, stormwater report | Medium |
| CHK-007 | Infiltration support | If infiltration is proposed, is infiltration testing included? | Test locations, rates, method, date | Soil report, infiltration testing log | High |
| CHK-008 | Soil and groundwater | Are soil and groundwater conditions documented where relevant? | Soil boring, seasonal high groundwater, limiting layer | Soil report, geotechnical report | High |
| CHK-009 | Outfall information | Are outfalls or discharge points identified? | Outfall labels, receiving water, discharge path | Site plans, drainage report | Medium |
| CHK-010 | Erosion controls | Are erosion and sediment controls shown? | Silt fence, inlet protection, construction entrance, stabilization | Erosion control plan, SWPPP | Medium |
| CHK-011 | Construction inspections | Does the package include inspection or corrective action expectations? | Inspection frequency or forms | SWPPP, permit checklist | Medium |
| CHK-012 | O&M plan | Is long-term operation and maintenance addressed? | Maintenance tasks, schedule, owner | O&M plan | High |
| CHK-013 | Maintenance owner | Is the responsible maintenance party identified? | Owner, HOA, municipality, private party | O&M plan, permit forms | High |
| CHK-014 | RFI closure | Are RFIs resolved or clearly tracked? | RFI status and response | RFI log | Medium |
| CHK-015 | Inspection closeout | Are inspection issues resolved? | Corrective action status | Inspection notes, corrective action log | High |

### 5.2 Recommended Status Values

Use these values throughout the system:

- `supported`
- `missing`
- `conflicting`
- `unclear`
- `not_applicable`
- `requires_human_review`

Avoid `approved` and `compliant` as system status values. Those words imply authority that the portfolio system should not claim.

### 5.3 Risk Categories

| Risk Category | Why It Matters | Trigger Evidence | Human Review Action |
| --- | --- | --- | --- |
| Missing drainage calculations | Calculations support runoff and BMP sizing | No calculation document found | Request calculations or confirm they are elsewhere |
| Mismatched storm event assumptions | Inconsistent criteria can invalidate review conclusions | Report says 25-year, calculations say 10-year | Confirm applicable standard and request correction |
| Missing infiltration testing | Infiltration BMPs depend on site-specific conditions | Infiltration proposed but no tests found | Request testing documentation or design revision |
| Missing soil or groundwater evidence | Subsurface conditions affect feasibility and safety | No boring or groundwater info found | Request geotechnical support |
| Missing erosion control details | Construction runoff can carry sediment and pollutants | No controls or phasing shown | Request erosion control plan revisions |
| Unclear outfall information | Discharge path affects downstream impact review | Outfall not labeled or receiving water unclear | Request outfall clarification |
| Missing O&M plan | Permanent BMPs require long-term maintenance | No O&M plan found | Request O&M plan |
| Missing maintenance owner | Unclear responsibility creates long-term failure risk | O&M tasks listed but no owner | Request responsible party |
| Unresolved RFI | Open RFIs can mean unresolved technical issues | RFI status is open | Hold finding pending response |
| Inspection issue without corrective action | Field issue may remain unresolved | Inspection note lists deficiency with no closeout | Request corrective action evidence |
| Inconsistent document references | Conflicting sheet, basin, or pipe IDs create confusion | Basin label differs across documents | Request consistency update |

## 6. GenAI System Design

Civil Engineer AI should use GenAI as one component inside a larger review system.

### 6.1 Appropriate AI Use Cases

Good AI use cases:

- Summarize uploaded project documents
- Answer source-linked questions about the uploaded package
- Extract candidate values, such as storm event names, BMP types, and maintenance owner references
- Compare retrieved evidence against checklist expectations
- Generate draft findings for human review
- Draft RFI or reviewer comment language
- Summarize unresolved issues
- Generate review memo sections using cited evidence

Poor or unsafe AI use cases:

- Approving a plan
- Certifying compliance
- Deciding whether a design is safe
- Replacing hydrologic or hydraulic calculation review
- Producing stamped conclusions
- Making final public safety determinations

### 6.2 Retrieval-Augmented Generation

RAG should be used whenever the system generates a finding. The model should not answer from general memory. It should receive:

- The checklist item being reviewed
- Retrieved project document chunks
- Retrieved municipal standard excerpts, if included
- Project metadata
- Output schema requirements
- Safety instructions

Every finding should include source references. If the retrieval service cannot find useful evidence, the system should mark the item as `missing`, `unclear`, or `requires_human_review` instead of inventing an answer.

### 6.3 Structured Extraction

The system should extract structured values where possible:

- Project type
- Disturbed area
- Proposed BMP types
- Design storm events
- Drainage area identifiers
- Basin identifiers
- Outfall labels
- Maintenance owner
- RFI status
- Inspection issue status

These extracted values should be treated as candidates until reviewed.

### 6.4 Human-in-the-Loop Review

Every AI-generated finding should be routed to a human review queue. The reviewer should be able to:

- Accept the finding
- Edit the finding
- Reject the finding
- Escalate the finding
- Mark it unclear
- Request more information

The system should log both the AI output and the human decision.

### 6.5 Audit Logging

Every important action should be auditable:

- Document upload
- Text extraction
- Chunk creation
- Embedding generation
- Retrieval query
- Retrieved chunks
- AI prompt version
- Model response
- Finding creation
- Human review action
- Evaluation result

This makes the project much stronger because it shows awareness of traceability and responsible AI design.

## 7. Safety and Professional Boundaries

Civil Engineer AI must be framed as a review-support system.

### 7.1 The System Must Not

- Approve engineering plans
- Certify compliance
- Stamp or seal drawings
- Replace a Professional Engineer
- Make final public safety determinations
- Claim a design is safe
- Claim a design is compliant without human confirmation
- Provide engineering calculations as final design work
- Make legal or regulatory determinations

### 7.2 Safe Wording

Use wording like:

- Potential issue
- Possible missing evidence
- Requires reviewer confirmation
- Source evidence not found
- Conflicting information detected
- Based on uploaded documents
- Recommended follow-up
- Draft reviewer comment
- Human review required

### 7.3 Prohibited Wording

Avoid wording like:

- Approved
- Certified
- Stamped
- Safe
- Fully compliant
- No further review needed
- Engineer-approved
- Meets all requirements

### 7.4 Why This Boundary Matters

Stormwater review affects public infrastructure, flooding risk, water quality, and long-term maintenance. Professional engineering ethics place public health, safety, and welfare at the center of practice. Civil Engineer AI should therefore avoid presenting itself as a substitute for licensed judgment.

## 8. Architecture Recommendations

The recommended architecture is a production-style vertical slice.

### 8.1 Frontend

Use Next.js with TypeScript.

Screens:

- Project dashboard
- Document library
- AI review workspace
- Checklist panel
- Finding detail page
- Human review queue
- Audit log
- Evaluation dashboard

### 8.2 Backend

Use FastAPI with Python.

Services:

- Project service
- Document ingestion service
- Retrieval service
- Checklist engine
- AI review assistant
- Risk flagging service
- Human review service
- Audit logger
- Evaluation service

### 8.3 Database

Use PostgreSQL with pgvector, either directly or through Supabase.

Core tables:

- `projects`
- `documents`
- `document_chunks`
- `checklist_items`
- `project_checklist_items`
- `review_runs`
- `findings`
- `finding_sources`
- `review_actions`
- `audit_events`
- `eval_cases`
- `eval_results`

### 8.4 AI Layer

Use OpenAI or Claude API.

The AI layer should:

- Receive structured prompts
- Use retrieved context only
- Return JSON output
- Include confidence and citations
- Avoid prohibited wording
- Require human review for uncertainty

### 8.5 Document Ingestion

V1 ingestion flow:

1. Upload or seed document.
2. Store document metadata.
3. Extract text.
4. Classify document type.
5. Chunk text.
6. Generate embeddings.
7. Store chunks and embeddings.
8. Log processing event.

### 8.6 Checklist Review Flow

1. Load project metadata.
2. Determine applicable checklist items.
3. Retrieve relevant document chunks for each item.
4. Ask the AI assistant to compare evidence against the checklist item.
5. Validate structured output.
6. Store finding and source references.
7. Route finding to human review.
8. Log the event.

## 9. Evaluation Plan

Civil Engineer AI should include an evaluation dashboard from the beginning. This is a major difference between a serious GenAI system and a simple demo.

### 9.1 Evaluation Metrics

| Metric | What It Measures |
| --- | --- |
| Source citation accuracy | Whether the cited source actually supports the finding |
| Checklist recall | Whether expected issues were found |
| Checklist precision | Whether generated findings were relevant |
| False positives | Findings generated when no issue exists |
| False negatives | Expected issues the system missed |
| Reviewer approval rate | Percentage of findings accepted by the reviewer |
| Reviewer rejection rate | Percentage of findings rejected by the reviewer |
| Unresolved risk count | Number of open high or medium risk issues |
| Unsupported claim count | Claims without source support |
| Prohibited wording count | Unsafe language such as approved or compliant |
| Response quality score | Human score for usefulness and clarity |

### 9.2 Mock Evaluation Dataset

Create three to five mock project packages.

#### Eval Case 1: Missing Infiltration Testing

Expected finding:

- Infiltration basin is proposed.
- No infiltration testing document is included.
- System should flag missing evidence.
- Risk level should be high.
- Human review should be required.

#### Eval Case 2: Mismatched Storm Event

Expected finding:

- Drainage report references a 25-year storm.
- Calculations reference a 10-year storm.
- System should flag conflicting assumptions.
- Risk level should be high.

#### Eval Case 3: Missing O&M Owner

Expected finding:

- O&M plan lists tasks and frequency.
- No responsible maintenance party is identified.
- System should flag missing ownership.
- Risk level should be high.

#### Eval Case 4: Unresolved Inspection Issue

Expected finding:

- Inspection note identifies sediment at inlet protection.
- No corrective action log is provided.
- System should flag unresolved issue.
- Risk level should be medium or high.

#### Eval Case 5: Clean Control Package

Expected finding:

- Required documents are present.
- Checklist items are mostly supported.
- System should avoid false positives.
- System should still avoid saying the project is approved.

## 10. Recommended V1 Portfolio Scope

The v1 build should focus on one end-to-end mock project.

### 10.1 Mock Project

Project name:

**Brookside Meadows Residential Subdivision Stormwater Review**

Project description:

A mock residential subdivision on a former farm parcel with new internal roads, 47 single-family lots, increased impervious surface, one proposed infiltration basin, one wet detention basin, bioretention areas, site grading changes, and a post-construction stormwater review package. See `BROOKSIDE_MEADOWS_PROJECT_STORY.md` for the full fixture.

### 10.2 Included Documents

Seed the project with synthetic documents:

- Site plan narrative
- Drainage report
- Stormwater calculations
- Geotechnical summary
- Erosion and sediment control plan
- O&M plan
- RFI log
- Inspection note
- Municipal checklist excerpt

### 10.3 Intentional Issues

Include these issues in the mock package:

- Infiltration basin proposed, but infiltration testing is missing.
- Drainage report uses one storm event and calculations use another.
- O&M tasks exist, but maintenance owner is unclear.
- Inspection note identifies a deficiency, but no corrective action closeout is included.
- Outfall label differs between site plan narrative and drainage report.

### 10.4 Minimum Screens

- Dashboard showing project status and open findings
- Document library showing processed files
- Checklist screen showing supported, missing, conflicting, and unclear items
- AI review workspace showing retrieved evidence and draft findings
- Human review queue showing accept/edit/reject/escalate actions
- Audit log showing traceability
- Evaluation dashboard showing test results

### 10.5 Minimum Backend Services

- Project service
- Document ingestion service
- Retrieval service
- Checklist engine
- AI review assistant
- Finding service
- Review action service
- Audit service
- Evaluation service

### 10.6 Minimum Database Tables

- `projects`
- `documents`
- `document_chunks`
- `checklist_items`
- `project_checklist_items`
- `review_runs`
- `findings`
- `finding_sources`
- `review_actions`
- `audit_events`
- `eval_cases`
- `eval_results`

## 11. Repo-Ready Deliverables

The repo should be organized so a recruiter can quickly understand the project.

```text
civil-engineer/
├── README.md
├── docs/
│   ├── RESEARCH_AND_SYSTEM_DESIGN.md
│   ├── ARCHITECTURE.md
│   ├── SAFETY_BOUNDARIES.md
│   ├── EVALUATION_PLAN.md
│   └── SAMPLE_PROJECT_PACKAGE.md
├── frontend/
├── backend/
├── data/
│   ├── mock-projects/
│   ├── sample-documents/
│   └── evaluation-cases/
└── screenshots/
```

### 11.1 README.md Outline

```md
# Civil Engineer AI: Stormwater Review Assistant

Civil Engineer AI is a portfolio GenAI system that assists stormwater and site-plan review by using document retrieval, checklist validation, risk flagging, human review, audit logging, and evaluation tracking.

## What It Demonstrates

- Retrieval-augmented generation
- Structured checklist validation
- Human-in-the-loop review
- Source-linked findings
- Audit logging
- Evaluation tracking
- Responsible AI boundaries

## What It Does Not Do

Civil Engineer AI does not approve plans, certify compliance, replace licensed engineers, stamp drawings, or make final safety determinations.

## Architecture

Next.js frontend, FastAPI backend, PostgreSQL with pgvector, document ingestion, retrieval service, AI review assistant, human review queue, audit logger, and evaluation dashboard.

## Demo Workflow

1. Load mock stormwater project.
2. Ingest project documents.
3. Run checklist-based AI review.
4. Inspect cited evidence.
5. Accept, edit, reject, or escalate findings.
6. Review audit log and evaluation metrics.
```

### 11.2 docs/RESEARCH_AND_SYSTEM_DESIGN.md Outline

This file should contain the full research and system design brief.

Sections:

- Project purpose
- Research basis
- Civil engineering workflow
- Document types
- Review checklist
- Risk categories
- GenAI design
- Safety boundaries
- Architecture recommendations
- Evaluation plan
- V1 scope
- References

### 11.3 docs/ARCHITECTURE.md Outline

Sections:

- System goals
- Non-goals
- High-level architecture
- Stack
- Core modules
- Data model
- Main system flows
- API surface
- Frontend screens
- AI prompting strategy
- Error handling
- Security boundaries
- V1 scope

### 11.4 docs/SAFETY_BOUNDARIES.md Outline

Sections:

- Professional boundaries
- Prohibited system claims
- Safe wording
- Human review requirements
- Source citation requirements
- Audit requirements
- Liability-aware project framing

### 11.5 docs/EVALUATION_PLAN.md Outline

Sections:

- Evaluation goals
- Evaluation fixtures
- Expected findings
- Metrics
- Pass/fail criteria
- Regression testing plan
- Prompt version tracking

### 11.6 docs/SAMPLE_PROJECT_PACKAGE.md Outline

Sections:

- Mock project overview
- Site conditions
- Submitted documents
- Intentional issues
- Expected findings
- Expected reviewer actions
- Sample seed data references

## 12. Implementation Recommendations

Start with documentation and seed data before building the full UI.

Recommended development sequence:

1. Create repo and docs.
2. Define mock project package.
3. Create checklist seed data.
4. Create synthetic sample documents.
5. Build backend data model.
6. Build document ingestion and chunking.
7. Add retrieval.
8. Add AI review output schema.
9. Add findings and human review queue.
10. Add audit logging.
11. Add evaluation cases.
12. Build polished frontend screens.

The first successful milestone should be one complete vertical slice, not the full platform.

## 13. Final System Positioning

Civil Engineer AI should be positioned as:

> A production-style GenAI portfolio system for stormwater review support. It combines structured project data, document retrieval, checklist validation, risk flagging, human review, audit logging, and evaluation tracking.

It should not be positioned as:

> An AI civil engineer that approves site plans.

The value of the project is that it demonstrates safe, realistic, and technically structured GenAI system design in a domain where professional judgment matters.

## References

[epa-construction]: https://www.epa.gov/npdes/stormwater-discharges-construction-activities "EPA: Stormwater Discharges from Construction Activities"

[epa-cgp-resources]: https://www.epa.gov/npdes/construction-general-permit-resources-tools-and-templates "EPA: Construction General Permit Resources, Tools, and Templates"

[epa-post-construction]: https://www.epa.gov/npdes/national-menu-best-management-practices-bmps-stormwater-post-construction "EPA: National Menu of BMPs for Stormwater Post-Construction"

[nspe-ethics]: https://www.nspe.org/career-growth/ethics/nspe-code-ethics-engineers "NSPE: Code of Ethics for Engineers"

[asce-ethics]: https://www.asce.org/career-growth/ethics/code-of-ethics "ASCE: Code of Ethics"
