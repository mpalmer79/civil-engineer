# Seed Data Plan, Civil Engineer AI

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Project fixture:** Brookside Meadows Residential Subdivision
**Purpose:** Seed-ready data for v1, a project object, a document table, a
stormwater checklist, expected findings, and evaluation cases. This is the
bridge from the Phase 0 story to a real database seed (Phase 2).

> All data is **synthetic**. The package intentionally contains gaps and
> conflicts (see `BROOKSIDE_MEADOWS_PROJECT_STORY.md` §7) so the review-support
> system has concrete, checkable findings. IDs use readable slugs for the seed;
> production may swap to UUIDs.

---

## 1. Project Seed Data

```json
{
  "project_id": "proj_brookside_meadows",
  "project_name": "Brookside Meadows Residential Subdivision",
  "project_type": "residential_subdivision",
  "location_context": "Suburban-fringe former farm parcel on the edge of an existing neighborhood",
  "acreage": 38.5,
  "disturbed_area_acres": 22.0,
  "proposed_lots": 47,
  "review_type": "subdivision_site_plan_with_post_construction_stormwater",
  "review_domain": "stormwater",
  "jurisdiction": "Town of Hartwell",
  "status": "ready_for_review",
  "has_infiltration_practice": true,
  "has_detention_basin": true,
  "site_conditions": [
    { "type": "soils", "description": "Hydrologic soil groups B and C with a band of slower C/D soils and a possible restrictive layer in the lower meadow." },
    { "type": "groundwater", "description": "Seasonal high groundwater ~2.5-3.5 ft below grade in the southeastern meadow." },
    { "type": "wetland_buffer", "description": "Delineated wetland along Brook Run with a 100-ft town buffer near proposed outfalls and grading." },
    { "type": "stream", "description": "Intermittent stream (Brook Run) crossing the SE corner toward the Quarry Road culvert." },
    { "type": "slope", "description": "~54 ft of fall NW to SE; 8-15% slopes along the western wood line." },
    { "type": "downstream_structure", "description": "Existing 36-inch RCP culvert under Quarry Road; reported downstream road-edge ponding in large storms." },
    { "type": "adjacent_use", "description": "Established Quarry Road Estates neighborhood abutting the south and east property lines." }
  ],
  "proposed_improvements": [
    { "type": "detention_basin", "label": "Basin 1", "aliases": ["Pond A"], "description": "Wet detention basin for peak-flow attenuation before the culvert outfall." },
    { "type": "infiltration_basin", "label": "Basin 2", "aliases": [], "description": "Infiltration basin in the meadow for volume reduction and recharge." },
    { "type": "bioretention", "label": "Bioretention Cells BR-1/BR-2", "aliases": [], "description": "Two roadside bioretention cells for water-quality treatment." },
    { "type": "storm_drain", "label": "Storm Drain Network", "aliases": [], "description": "Curb inlets, catch basins, and storm drain pipe (material in dispute via open RFI)." },
    { "type": "riprap_apron", "label": "Outlet Protection", "aliases": [], "description": "Riprap aprons at the basin outlet and culvert headwall." }
  ],
  "known_constraints": [
    "Infiltration feasibility vs. shallow seasonal high groundwater",
    "Downstream culvert capacity and reported ponding",
    "Wetland buffer encroachment near outfalls",
    "Phased clearing of 22 acres on slopes draining to a stream",
    "Long-term maintenance ownership of shared facilities"
  ]
}
```

---

## 2. Document Seed Data

`status` ∈ `present`, `partial`, `missing`, `referenced_not_included`,
`not_yet_submitted`.

| document_id | file_name | document_type | status | purpose | expected_key_information | intentionally_missing_or_conflicting_information |
| --- | --- | --- | --- | --- | --- |
| `doc_site_narrative` | `site-plan-narrative.pdf` | site_plan_narrative | present | Describe the project and stormwater approach | Project scope, phasing intent, BMP strategy | References revised sheet C-3.1 (not included) |
| `doc_existing_conditions` | `existing-conditions-plan.pdf` | existing_conditions_plan | present | Show pre-development site | Topography, wood line, meadow, stream, wetland, culvert |, |
| `doc_layout_plan` | `layout-plan.pdf` | layout_plan | present | Show lots and roads | 47 lots, Brookside Drive, loop, Meadow Court cul-de-sac, sidewalks |, |
| `doc_grading_drainage` | `grading-and-drainage-plan.pdf` | grading_drainage_plan | present | Show grading and storm system | Grading, storm drain, basin locations | Labels basin "Pond A" (conflicts with report's "Basin 1") |
| `doc_utility_plan` | `utility-plan.pdf` | utility_plan | present | Show utilities | Water main, gravity sewer, pump station, dry utilities |, |
| `doc_stormwater_report` | `stormwater-management-report.pdf` | stormwater_management_report | present | Describe permanent stormwater controls | BMP selection, treatment train, basin sizing | Uses **25-year** design storm; calls basin "Basin 1"; does not address groundwater separation |
| `doc_hydrology_calcs` | `hydrology-calculations.pdf` | hydrology_calculations | present | Runoff/peak-flow calcs | CN, Tc, peak flows existing vs. proposed |, |
| `doc_hydraulic_calcs` | `hydraulic-calculations.pdf` | hydraulic_calculations | partial | Pipe/outlet sizing | Pipe capacity, outlet structure sizing | **No downstream culvert capacity analysis** |
| `doc_soils_report` | `soils-geotechnical-report.pdf` | soil_report | present | Subsurface conditions | Soil groups, borings, seasonal high groundwater | Notes seasonal high groundwater (separation never reconciled in stormwater report) |
| `doc_infiltration_logs` | `infiltration-testing-logs.pdf` | infiltration_testing_documentation | missing | Support the infiltration basin | Test locations, rates, method, date, depth to GW | **Missing/incomplete** for a proposed infiltration practice |
| `doc_escp` | `erosion-sediment-control-plan.pdf` | erosion_control_plan | present | Construction-phase controls | Silt fence, inlet protection, construction entrance, stabilization | **Not clearly tied to construction phasing** |
| `doc_swppp` | `swppp.pdf` | swppp | present | Construction stormwater pollution prevention | Controls, inspection commitments, corrective-action procedure | Template-level; light on site-specific detail |
| `doc_oem_plan` | `operation-maintenance-plan.pdf` | o_and_m_plan | present | Long-term BMP maintenance | Tasks, frequency, access, responsible owner | References "HOA maintenance" but **HOA responsibility not formally documented** |
| `doc_phasing_plan` | `construction-phasing-plan.pdf` | construction_phasing_plan | present | Construction sequence | Two phases: upland then lower meadow | Inconsistent with the E&SC plan's sequencing |
| `doc_inspection_notes` | `inspection-notes.pdf` | inspection_notes | present | Field observations | Date, inspector, observations | Flags **sediment at basin outlet; no corrective action logged** |
| `doc_rfi_log` | `rfi-log.pdf` | rfi_log | present | Track questions | RFI number, question, status | RFI asks **pipe material; no response recorded** |
| `doc_municipal_checklist` | `town-stormwater-checklist.pdf` | municipal_checklist | present | Town submission requirements | Required reports, design-storm standard, O&M requirement | Expects a **different design storm** than the report's 25-year |
| `doc_comment_response` | `comment-response-letter.pdf` | comment_response_letter | not_yet_submitted | Respond to review comments | Responses to each comment | First submission, none yet |
| `doc_revised_c31` | `grading-sheet-C-3.1-REV.pdf` | grading_drainage_plan | referenced_not_included | Revised grading sheet | Revised grading per narrative | **Referenced but absent from the package** |

---

## 3. Checklist Seed Data

Reusable stormwater checklist items. `expected_status_for_brookside_meadows`
shows the intended ground-truth status for this fixture (drives evaluation).

| checklist_item_id | category | requirement | expected_evidence | supporting_documents | risk_level | applies_when | expected_status_for_brookside_meadows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `chk_pkg_completeness` | completeness | Package includes a stormwater/drainage report | Stormwater or drainage report present | stormwater_management_report | high | always | supported |
| `chk_design_storm_stated` | design_storm | Design-storm assumptions are stated | Storm event, recurrence, rainfall depth | stormwater_management_report, hydrology_calculations | high | always | supported |
| `chk_design_storm_consistent` | design_storm | Design storm matches the municipal standard and is consistent across documents | Same event in report, calcs, and town checklist | stormwater_management_report, hydrology_calculations, municipal_checklist | high | always | **conflicting** (I-1) |
| `chk_drainage_areas` | drainage_areas | Existing and proposed drainage areas identified | Drainage area maps/tables | existing_conditions_plan, grading_drainage_plan, hydrology_calculations | medium | always | supported |
| `chk_runoff_calcs` | runoff | Runoff calcs for existing and proposed conditions | Peak flow / volume calcs | hydrology_calculations | high | always | supported |
| `chk_bmp_identified` | bmp | Proposed stormwater BMPs are identified | BMP type, location, purpose | stormwater_management_report, grading_drainage_plan | medium | always | supported |
| `chk_infiltration_testing` | infiltration | If infiltration is proposed, infiltration testing is included | Test locations, rates, method, date | soil_report, infiltration_testing_documentation | high | has_infiltration_practice | **missing** (I-2) |
| `chk_groundwater_separation` | infiltration | Separation to seasonal high groundwater is addressed for infiltration/bioretention | GW depth + separation discussion | soil_report, stormwater_management_report | high | has_infiltration_practice | **unclear** (I-3) |
| `chk_soil_groundwater_doc` | soils | Soil and groundwater conditions are documented | Borings, soil groups, SHGW | soil_report | high | always | supported |
| `chk_outfall_identified` | outfall | Outfalls/discharge points identified | Outfall labels, receiving water, path | grading_drainage_plan, stormwater_management_report | medium | always | supported |
| `chk_downstream_capacity` | downstream | Downstream conveyance capacity is discussed where a downstream structure exists | Downstream culvert capacity analysis | hydraulic_calculations, stormwater_management_report | high | has_downstream_structure | **missing** (I-4) |
| `chk_erosion_controls` | erosion | Erosion and sediment controls are shown | Silt fence, inlet protection, entrance, stabilization | erosion_control_plan, swppp | medium | always | supported |
| `chk_escp_phasing` | erosion | E&SC measures are tied to construction phasing | Phased control sequencing | erosion_control_plan, construction_phasing_plan | medium | always | **conflicting** (I-6) |
| `chk_oem_plan` | o_and_m | Long-term operation & maintenance is addressed | Tasks, schedule, access | o_and_m_plan | high | has_detention_basin OR has_infiltration_practice | supported |
| `chk_oem_owner` | o_and_m | Responsible maintenance party is clearly identified | Named owner (HOA/municipality/private) with binding responsibility | o_and_m_plan, site_plan_narrative | high | always | **unclear** (I-5) |
| `chk_rfi_closure` | rfi | RFIs are resolved or clearly tracked | RFI status and response | rfi_log | medium | always | **conflicting/unclear** (I-8) |
| `chk_inspection_closeout` | inspection | Inspection deficiencies have corrective-action closeout | Corrective action status | inspection_notes | high | always | **unresolved** (I-7) |
| `chk_reference_consistency` | consistency | Basin/sheet/structure references are consistent across documents | Matching labels across plan and report | grading_drainage_plan, stormwater_management_report | medium | always | **conflicting** (I-9) |
| `chk_referenced_sheets_present` | completeness | Referenced revised sheets are included in the package | All cited sheets present | site_plan_narrative, grading_drainage_plan | medium | always | **missing** (I-10) |

> 19 items, comfortably within the 12 to 20 target. `applies_when` predicates use
> the project flags in §1 plus a derived `has_downstream_structure` (true when a
> `downstream_structure` site condition exists).

---

## 4. Expected Findings Seed Data

These are the findings the AI review is expected to produce (ground truth for
evaluation). Each maps to a planted issue (I-#) and a checklist item.

| finding_id | title | category | risk_level | expected_status | evidence_to_find | reason_it_matters | recommended_human_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `find_storm_conflict` | Design-storm assumption conflicts with town standard | design_storm | high | conflicting | Report states 25-year; town checklist expects a different event | Inconsistent criteria can invalidate review conclusions | Confirm applicable standard; request correction/clarification |
| `find_infiltration_missing` | Infiltration testing not found for proposed infiltration basin | infiltration | high | missing | Infiltration basin proposed; no testing logs in package | Infiltration BMPs depend on site-specific testing | Request field infiltration testing or a design revision |
| `find_gw_separation` | Groundwater separation for infiltration not addressed | infiltration | high | unclear | Soils report notes SHGW; report omits separation | Inadequate separation undermines infiltration feasibility | Request separation analysis referencing SHGW |
| `find_downstream_capacity` | Downstream culvert capacity not analyzed | downstream | high | missing | Culvert referenced; no downstream capacity analysis | Post-development flows could worsen downstream ponding | Request downstream conveyance analysis |
| `find_oem_owner` | Maintenance owner not clearly bound | o_and_m | high | unclear | O&M cites "HOA" without documented responsibility | Unclear responsibility creates long-term failure risk | Request formal HOA maintenance responsibility |
| `find_escp_phasing` | E&SC sequencing not tied to phasing | erosion | medium | conflicting | E&SC plan lacks phased sequencing vs. phasing plan | Sediment risk on phased slope clearing | Request phased E&SC sequencing |
| `find_inspection_open` | Inspection deficiency without corrective action | inspection | high | unresolved | Sediment at basin outlet noted; no corrective action | Field issue may remain unresolved | Request corrective-action evidence/closeout |
| `find_rfi_open` | Open RFI on pipe material with no response | rfi | medium | conflicting | RFI asks pipe material; no response recorded | Open RFI may signal an unresolved design detail | Hold pending response; confirm pipe material |
| `find_basin_naming` | Inconsistent basin naming across documents | consistency | medium | conflicting | "Pond A" (grading) vs. "Basin 1" (report) | Conflicting labels create review confusion | Request consistent naming |
| `find_missing_sheet` | Referenced revised sheet C-3.1 not included | completeness | medium | missing | Narrative cites revised C-3.1; sheet absent | Cannot review a cited revision that is missing | Request the missing revised sheet |

A correct v1 also produces **`supported`** findings for the clean items
(completeness, drainage areas, runoff calcs, BMP identification, outfalls, soil
documentation, erosion controls present), and **never** emits `approved` /
`compliant` / `safe`.

---

## 5. Evaluation Cases

Eight cases. Each isolates one meaningful system behavior. `input_documents`
lists the documents provided to the case (a subset or the full package).
`evaluation_metric` is the primary metric scored; recall/precision and
citation-accuracy are computed for all.

```json
[
  {
    "eval_case_id": "eval_infiltration_missing",
    "name": "Missing infiltration testing",
    "input_documents": ["doc_stormwater_report", "doc_soils_report"],
    "expected_findings": [
      { "checklist_item_id": "chk_infiltration_testing", "expected_status": "missing", "finding_id": "find_infiltration_missing" }
    ],
    "expected_risk_level": "high",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_storm_conflict",
    "name": "Conflicting design-storm assumption",
    "input_documents": ["doc_stormwater_report", "doc_hydrology_calcs", "doc_municipal_checklist"],
    "expected_findings": [
      { "checklist_item_id": "chk_design_storm_consistent", "expected_status": "conflicting", "finding_id": "find_storm_conflict" }
    ],
    "expected_risk_level": "high",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_oem_owner",
    "name": "Missing O&M responsibility",
    "input_documents": ["doc_oem_plan", "doc_site_narrative"],
    "expected_findings": [
      { "checklist_item_id": "chk_oem_owner", "expected_status": "unclear", "finding_id": "find_oem_owner" }
    ],
    "expected_risk_level": "high",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_rfi_open",
    "name": "Unresolved RFI (pipe material)",
    "input_documents": ["doc_rfi_log"],
    "expected_findings": [
      { "checklist_item_id": "chk_rfi_closure", "expected_status": "conflicting", "finding_id": "find_rfi_open" }
    ],
    "expected_risk_level": "medium",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_downstream_capacity",
    "name": "Missing downstream capacity discussion",
    "input_documents": ["doc_hydraulic_calcs", "doc_stormwater_report", "doc_existing_conditions"],
    "expected_findings": [
      { "checklist_item_id": "chk_downstream_capacity", "expected_status": "missing", "finding_id": "find_downstream_capacity" }
    ],
    "expected_risk_level": "high",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_inspection_open",
    "name": "Inspection note without corrective action",
    "input_documents": ["doc_inspection_notes"],
    "expected_findings": [
      { "checklist_item_id": "chk_inspection_closeout", "expected_status": "unresolved", "finding_id": "find_inspection_open" }
    ],
    "expected_risk_level": "high",
    "evaluation_metric": "recall"
  },
  {
    "eval_case_id": "eval_basin_naming",
    "name": "Conflicting basin names",
    "input_documents": ["doc_grading_drainage", "doc_stormwater_report"],
    "expected_findings": [
      { "checklist_item_id": "chk_reference_consistency", "expected_status": "conflicting", "finding_id": "find_basin_naming" }
    ],
    "expected_risk_level": "medium",
    "evaluation_metric": "source_citation_accuracy"
  },
  {
    "eval_case_id": "eval_clean_control",
    "name": "Clean control, no false positives",
    "input_documents": ["doc_existing_conditions", "doc_layout_plan", "doc_hydrology_calcs"],
    "expected_findings": [],
    "expected_risk_level": "low",
    "evaluation_metric": "no_false_positive"
  }
]
```

> The `eval_clean_control` case is deliberately built from documents with **no
> planted defect** so it tests restraint: the system should produce no invented
> findings and must not claim approval or compliance. An optional ninth/tenth
> case can target `chk_groundwater_separation` (I-3) and
> `chk_referenced_sheets_present` (I-10) once the others pass.

---

## 6. How This Seed Maps to the Build

- **Phase 1 (static):** these objects render the dashboard, document library,
  checklist, and findings without any model calls.
- **Phase 2 (backend):** the same JSON/tables become database seed scripts
  matching `DOMAIN_MODEL.md`.
- **Phase 3 (retrieval):** each document needs synthetic body text (a short
  narrative per `expected_key_information`) so chunks and embeddings are real.
- **Phase 4 (AI):** the checklist items become per-item prompts; expected
  findings are the target outputs.
- **Phase 5 (evaluation):** Section 5 cases plug directly into the evaluation
  harness; Section 4 expected findings are the ground truth.

**Next data task (Phase 1/3):** author short synthetic document bodies (1 to 2
pages each) for the `present`/`partial` documents so retrieval has real text to
chunk. Keep the planted issues intact and keep all content clearly fictional.
