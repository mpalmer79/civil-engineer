# DXF Integration Test Report

Snapshot: brookside-proof-v1

Synthetic Brookside Meadows subdivision drawing processed through the real Civil Engineer AI upload, validation, storage, parse, and retrieval services. The drawing is synthetic review-support data: conceptual geometry, no survey accuracy, not for construction.

## Scope statement

This result demonstrates deterministic DXF metadata extraction, consistency checking, reference identification, and reviewer-support analysis. It does not verify CAD, validate design, certify compliance, or approve plans. Every finding needs human review.

## Environment

* Parser: ezdxf 1.4.4
* Backend: FastAPI test client over the production route handlers
* Database: throwaway SQLite seeded with the Brookside Meadows fixture
* Drawing units: feet (declared by the DXF header)

## Pipeline exercised

1. File upload (POST /api/v1/projects/{id}/cad-files/upload, backend/app/api/v1/cad_intake.py)
2. Intake validation (validate_cad_upload_file, backend/app/services/cad_intake_service.py)
3. Safe storage registration (save_uploaded_dxf_file, backend/app/services/cad_intake_service.py)
4. DXF parse request (POST /api/v1/cad-files/{id}/parse, backend/app/api/v1/cad_intake.py)
5. ezdxf processing (parse_dxf_file, backend/app/services/cad_intake_service.py)
6. Layer extraction and classification (classify_layer, backend/app/services/cad/layer_taxonomy.py)
7. Entity extraction with safe bounds (entity_bounds, backend/app/services/cad/geometry.py)
8. Text extraction (_entity_text, backend/app/services/cad_intake_service.py)
9. Block extraction (CadBlockExtract, backend/app/services/cad_intake_service.py)
10. Reference parsing (parse_references, backend/app/services/cad/reference_parser.py)
11. Facility identity and review-support findings (detect_facility_conflicts, backend/app/services/cad/facility_identity.py)
12. Database persistence (SQLAlchemy models, backend/app/db/models.py)
13. Reviewer-facing result retrieval (GET /api/v1/cad-parse-runs/{id}/summary, backend/app/api/v1/cad_intake.py)

## Results

| Metric | Value |
| --- | --- |
| Upload HTTP status | 200 |
| Intake validation | accepted |
| Parse status | completed |
| Entities | 168 |
| Layers | 15 |
| Blocks | 5 |
| Text records | 80 |
| Reference candidates | 16 |
| Review-support findings | 8 |
| Matched references | 3 |
| Missing or ambiguous references | 2 |

## Checks

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| upload_http_status | 200 | 200 | pass |
| validation_status | accepted | accepted | pass |
| parse_http_status | 200 | 200 | pass |
| parse_status | completed | completed | pass |
| entity_count | 168 | 168 | pass |
| layer_count | 15 | 15 | pass |
| block_count | 5 | 5 | pass |
| text_count | 80 | 80 | pass |
| reference_candidates | 16 | 16 | pass |
| findings | 8 | 8 | pass |
| matched_references | 3 | 3 | pass |
| missing_references | 1 | 1 | pass |
| ambiguous_references | 1 | 1 | pass |
| reference:sheet_reference:C-3.1 | matched | matched | pass |
| reference:sheet_reference:C-5.0 | matched | matched | pass |
| reference:detail_reference:C-5.0 | matched | matched | pass |
| reference:sheet_reference:C-9.9 | missing | missing | pass |
| reference:detail_reference:C-4.X | ambiguous | ambiguous | pass |
| layer:0 | unknown | unknown | pass |
| layer:Defpoints | unknown | unknown | pass |
| layer:C-PROP | property_boundary | property_boundary | pass |
| layer:C-ROAD | road_alignment | road_alignment | pass |
| layer:C-LOTS | lots_parcels | lots_parcels | pass |
| layer:C-LABEL | annotation | annotation | pass |
| layer:C-LANDSCAPE | landscape | landscape | pass |
| layer:C-GRAD | grading | grading | pass |
| layer:C-STRM | stormwater | stormwater | pass |
| layer:C-WETL | wetland_buffer | wetland_buffer | pass |
| layer:C-EROS | erosion_control | erosion_control | pass |
| layer:C-UTIL | utilities | utilities | pass |
| layer:V-MISC | unknown | unknown | pass |
| layer:X-EXPORT | unknown | unknown | pass |
| layer:DRAFT-01 | unknown | unknown | pass |
| block_names | ['LOT_MARKER', 'NORTH_ARROW', 'STORM_MANHOLE', 'TITLEBLOCK_FRAME', 'TREE_SYMBOL'] | ['LOT_MARKER', 'NORTH_ARROW', 'STORM_MANHOLE', 'TITLEBLOCK_FRAME', 'TREE_SYMBOL'] | pass |
| findings:missing_plan_sheet_match | 1 | 1 | pass |
| findings:unclear_detail_reference | 1 | 1 | pass |
| findings:possible_label_conflict | 3 | 3 | pass |
| findings:unknown_layer_category | 3 | 3 | pass |
| detention_vs_infiltration_not_paired | False | False | pass |
| common_layers_not_flagged_unknown | [] | [] | pass |
| invert_elevation_not_a_reference | False | False | pass |
| facility_labels | ['BIORETENTION AREA 3', 'DETENTION BASIN 1', 'INFILTRATION BASIN 1', 'NORTH DETENTION BASIN 2', 'OUTLET STRUCTURE 1', 'POND A', 'RAIN GARDEN 3', 'SOUTH DETENTION BASIN 2', 'WET POND A'] | ['BIORETENTION AREA 3', 'DETENTION BASIN 1', 'INFILTRATION BASIN 1', 'NORTH DETENTION BASIN 2', 'OUTLET STRUCTURE 1', 'POND A', 'RAIN GARDEN 3', 'SOUTH DETENTION BASIN 2', 'WET POND A'] | pass |

## Known limitations

* Reference matching runs against the seeded Brookside Meadows plan-sheet index; a project without an index cannot distinguish missing from unindexed.
* Paper-space entities are inventoried in the parse audit metadata, not persisted per entity.
* Geometry bounds for splines, ellipses, hatches, and dimensions are safe overestimates, not exact envelopes.
* The drawing is synthetic and conceptual; no surveyed accuracy is implied.

## Reproduce

```
python scripts/run_dxf_proof.py
```

The generator (scripts/generate_brookside_proof_dxf.py) and this harness are deterministic; regenerating produces identical bytes on the same parser version.
