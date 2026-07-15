# DXF Validation

This is the canonical reference for the DXF proof of concept. It folds in the
former DXF proof-of-concept, test-methodology, limitations, and artifact-manifest
documents. The public page is at `/proof-of-concept`. The generated integration
report at `public/proof-of-concept/dxf/` is produced by
`scripts/run_dxf_proof.py` and is never hand-edited.

## Purpose

Prove, through reproducible evidence, that Civil Engineer AI can ingest a
structurally valid civil-site DXF, extract useful metadata, identify references
and review-support observations, and organize results for human review. The proof
demonstrates deterministic DXF metadata extraction, consistency checking,
reference identification, and reviewer-support analysis. It does not demonstrate
engineering correctness, design validation, compliance, or approval.

## The synthetic drawing

`brookside_meadows_realistic_submission.dxf` is produced by the script
`scripts/generate_brookside_proof_dxf.py`. It is a conceptual subdivision plan
for the synthetic Brookside Meadows case study in the fictional Town of Hartwell:
47 conceptual lots, a road alignment with a cul-de-sac, grading contours with
elevation labels, a wetland boundary and 50 ft buffer, a detention basin and an
infiltration basin, storm pipes and an outfall, five reusable blocks, declared
units of feet, sheet references (including an intentionally missing C-9.9 and an
intentionally ambiguous detail reference), facility labels that intentionally
share a number without being the same facility, and three intentionally
unclassifiable layers. The geometry is conceptual: not surveyed, not
georeferenced, and not suitable for construction.

## Methodology and ground truth

The harness `scripts/run_dxf_proof.py` regenerates the DXF, uploads and parses it
through the real FastAPI upload and parse routes, and compares the results against
the versioned ground truth in `scripts/dxf_proof_expected.json`. The verified run
produces exactly:

| Metric | Value |
| --- | --- |
| Upload HTTP result | 200 |
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

The public page renders from the generated artifact, never from copies of the
numbers, and fails visibly if the artifact and the displayed metrics disagree.

## Assertions and artifact manifest

The harness regenerates four downloadable artifacts and a manifest: the DXF, the
structured JSON result, the Markdown integration report, and a ZIP bundle. Each
is served through an allowlisted download route and listed in the manifest with
its size and SHA-256 hash. Continuous integration runs the harness and then fails
if the committed artifacts under `public/proof-of-concept` differ by a single
byte, so the published hashes always match the committed bytes.

## Reproducibility and hash verification

The generator and harness are byte-deterministic. Anyone can rerun
`scripts/run_dxf_proof.py`, regenerate the artifacts, and confirm the SHA-256
hashes match the manifest. The originally supplied binary proof artifacts were
not available in the build environment; the committed artifacts were regenerated
from the known synthetic Brookside scenario by this deterministic harness, and no
claim is made that the original binary files were used.

## What is and is not proven

Proven: valid DXF intake, real parser execution, entity and layer inventory, text
and block extraction, reference identification against the plan-sheet index,
persistence, reviewer-facing retrieval, and deterministic finding generation.

Not proven: basin sizing, pipe slope, hydraulic capacity, grading, regulatory
compliance, construction readiness, design safety, plan approval, survey
accuracy, or complete CAD semantic understanding. The proof validates the intake
pipeline, not engineering design. Every finding it produces still needs human
review.
