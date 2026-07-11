"""Run the reproducible DXF proof-of-concept harness.

Generates the synthetic Brookside Meadows DXF, uploads it through the real
FastAPI upload endpoint, requests parsing through the real parse endpoint,
retrieves the persisted results, compares them against the versioned ground
truth in scripts/dxf_proof_expected.json, and writes the four public proof
artifacts plus the artifact manifest:

* brookside_meadows_realistic_submission.dxf
* brookside_meadows_dxf_test_result.json
* DXF_INTEGRATION_TEST_REPORT.md
* civil_engineer_dxf_test_bundle.zip
* manifest.json

Every check must pass or the process exits nonzero. The production parser is
never bypassed: the harness talks to the same routes the browser uses.

All artifacts are deterministic: the DXF generator pins volatile metadata,
the structured result excludes database identifiers and timestamps, the
report is derived from the structured result, and the ZIP uses fixed entry
timestamps. Regenerating on the same parser version produces identical bytes,
which is what the CI proof job asserts.

The harness demonstrates deterministic DXF metadata extraction, consistency
checking, reference identification, and reviewer-support analysis. It does
not verify CAD, validate design, certify compliance, or approve anything.

Run from the repository root: python scripts/run_dxf_proof.py
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
OUTPUT_DIR = REPO_ROOT / "public" / "proof-of-concept" / "dxf"
EXPECTED_PATH = REPO_ROOT / "scripts" / "dxf_proof_expected.json"

PROJECT_ID = "proj_brookside_meadows"
SNAPSHOT_ID = "brookside-proof-v1"
ZIP_ENTRY_DATE = (2026, 1, 1, 0, 0, 0)

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _configure_isolated_backend() -> None:
    """Point the backend at throwaway storage before importing it."""

    db_fd, db_path = tempfile.mkstemp(prefix="dxf_proof_", suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["CAD_UPLOAD_DIR"] = tempfile.mkdtemp(prefix="dxf_proof_cad_")
    os.environ.setdefault("AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS", "false")
    os.environ.setdefault("AUTH_DEMO_MODE", "true")
    os.environ.setdefault("AUTH_ALLOW_PUBLIC_DEMO", "true")
    os.environ.setdefault("AUTH_SECRET_KEY", "dxf-proof-harness")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _match_state(candidate: dict) -> str:
    if candidate["reference_type"] not in {
        "sheet_reference",
        "detail_reference",
    }:
        return "extracted_label"
    if candidate.get("matched_plan_sheet_id"):
        return "matched"
    reason = (candidate.get("match_reason") or "").lower()
    if "unresolved" in reason or "ambiguous" in reason:
        return "ambiguous"
    return "missing"


def run_harness() -> tuple[dict, list[dict]]:
    """Execute the proof pipeline and return (structured_result, checks)."""

    _configure_isolated_backend()

    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.cad import layer_taxonomy
    from generate_brookside_proof_dxf import (
        FIXTURE_VERSION,
        build_dxf_text,
    )

    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    dxf_text = build_dxf_text()
    dxf_bytes = dxf_text.encode("utf-8")

    checks: list[dict] = []

    def check(name: str, expected_value, actual_value) -> None:
        checks.append(
            {
                "check": name,
                "expected": expected_value,
                "actual": actual_value,
                "pass": expected_value == actual_value,
            }
        )

    with TestClient(app) as client:
        upload = client.post(
            f"/api/v1/projects/{PROJECT_ID}/cad-files/upload",
            files={
                "file": (
                    "brookside_meadows_realistic_submission.dxf",
                    dxf_bytes,
                    "application/dxf",
                )
            },
            data={"uploaded_by": "DXF proof harness"},
        )
        check(
            "upload_http_status",
            expected["intake"]["upload_http_status"],
            upload.status_code,
        )
        payload = upload.json()
        check(
            "validation_status",
            expected["intake"]["validation_status"],
            payload["validation_status"],
        )
        cad_file_id = payload["cad_file"]["cad_file_id"]

        parse = client.post(f"/api/v1/cad-files/{cad_file_id}/parse")
        check("parse_http_status", 200, parse.status_code)
        run = parse.json()
        run_id = run["parse_run_id"]
        check("parse_status", expected["intake"]["parse_status"], run["status"])

        layers = client.get(f"/api/v1/cad-parse-runs/{run_id}/layers").json()
        entities = client.get(
            f"/api/v1/cad-parse-runs/{run_id}/entities"
        ).json()
        blocks = client.get(f"/api/v1/cad-parse-runs/{run_id}/blocks").json()
        candidates = client.get(
            f"/api/v1/cad-parse-runs/{run_id}/reference-candidates"
        ).json()
        findings = [
            f
            for f in client.get(
                f"/api/v1/projects/{PROJECT_ID}/cad-review-findings"
            ).json()
            if f["parse_run_id"] == run_id
        ]

    counts = expected["counts"]
    check("entity_count", counts["entities"], run["entity_count"])
    check("layer_count", counts["layers"], run["layer_count"])
    check("block_count", counts["blocks"], run["block_count"])
    check("text_count", counts["text_records"], run["text_count"])
    check("reference_candidates", counts["reference_candidates"], len(candidates))
    check("findings", counts["findings"], len(findings))

    reference_states = {
        (c["normalized_reference"], c["reference_type"]): _match_state(c)
        for c in candidates
    }
    matched = sum(1 for s in reference_states.values() if s == "matched")
    missing = sum(1 for s in reference_states.values() if s == "missing")
    ambiguous = sum(1 for s in reference_states.values() if s == "ambiguous")
    check("matched_references", counts["matched_references"], matched)
    check("missing_references", counts["missing_references"], missing)
    check("ambiguous_references", counts["ambiguous_references"], ambiguous)

    for ref in expected["expected_references"]:
        state = reference_states.get((ref["normalized"], ref["type"]))
        check(
            f"reference:{ref['type']}:{ref['normalized']}",
            ref["state"],
            state,
        )

    layer_categories = {
        layer["layer_name"]: layer["review_category"] for layer in layers
    }
    for name, category in expected["expected_layer_categories"].items():
        check(f"layer:{name}", category, layer_categories.get(name))

    block_names = sorted(b["block_name"] for b in blocks)
    check("block_names", expected["expected_block_names"], block_names)

    findings_by_type = Counter(f["finding_type"] for f in findings)
    for finding_type, count in expected["expected_findings_by_type"].items():
        check(
            f"findings:{finding_type}", count, findings_by_type.get(finding_type, 0)
        )

    # Forbidden false positives.
    conflict_descriptions = [
        f["description"]
        for f in findings
        if f["finding_type"] == "possible_label_conflict"
    ]
    basin_pairing = any(
        "DETENTION BASIN 1" in d and "INFILTRATION BASIN 1" in d
        for d in conflict_descriptions
    )
    check("detention_vs_infiltration_not_paired", False, basin_pairing)

    flagged_layers = {
        f["title"].split("'")[1]
        for f in findings
        if f["finding_type"] == "unknown_layer_category" and "'" in f["title"]
    }
    common_flagged = sorted(
        flagged_layers
        & {"C-PROP", "C-ROAD", "C-LOTS", "C-LABEL", "C-LANDSCAPE"}
    )
    check("common_layers_not_flagged_unknown", [], common_flagged)

    invert_as_reference = any(
        "638.2" in c["normalized_reference"] for c in candidates
    )
    check("invert_elevation_not_a_reference", False, invert_as_reference)

    facility_labels = sorted(
        c["normalized_reference"]
        for c in candidates
        if c["reference_type"] == "basin_label"
    )
    check(
        "facility_labels", expected["expected_facility_labels"], facility_labels
    )

    entity_types = Counter(e["entity_type"] for e in entities)

    from app import __name__ as _app_name  # noqa: F401  (import proof)
    import ezdxf

    structured = {
        "snapshot_id": SNAPSHOT_ID,
        "fixture_version": FIXTURE_VERSION,
        "synthetic": True,
        "parser": {"name": "ezdxf", "version": ezdxf.__version__},
        "drawing_units": expected["drawing_units"],
        "pipeline": [
            {
                "stage": "File upload",
                "boundary": "POST /api/v1/projects/{id}/cad-files/upload",
                "module": "backend/app/api/v1/cad_intake.py",
            },
            {
                "stage": "Intake validation",
                "boundary": "validate_cad_upload_file",
                "module": "backend/app/services/cad_intake_service.py",
            },
            {
                "stage": "Safe storage registration",
                "boundary": "save_uploaded_dxf_file",
                "module": "backend/app/services/cad_intake_service.py",
            },
            {
                "stage": "DXF parse request",
                "boundary": "POST /api/v1/cad-files/{id}/parse",
                "module": "backend/app/api/v1/cad_intake.py",
            },
            {
                "stage": "ezdxf processing",
                "boundary": "parse_dxf_file",
                "module": "backend/app/services/cad_intake_service.py",
            },
            {
                "stage": "Layer extraction and classification",
                "boundary": "classify_layer",
                "module": "backend/app/services/cad/layer_taxonomy.py",
            },
            {
                "stage": "Entity extraction with safe bounds",
                "boundary": "entity_bounds",
                "module": "backend/app/services/cad/geometry.py",
            },
            {
                "stage": "Text extraction",
                "boundary": "_entity_text",
                "module": "backend/app/services/cad_intake_service.py",
            },
            {
                "stage": "Block extraction",
                "boundary": "CadBlockExtract",
                "module": "backend/app/services/cad_intake_service.py",
            },
            {
                "stage": "Reference parsing",
                "boundary": "parse_references",
                "module": "backend/app/services/cad/reference_parser.py",
            },
            {
                "stage": "Facility identity and review-support findings",
                "boundary": "detect_facility_conflicts",
                "module": "backend/app/services/cad/facility_identity.py",
            },
            {
                "stage": "Database persistence",
                "boundary": "SQLAlchemy models",
                "module": "backend/app/db/models.py",
            },
            {
                "stage": "Reviewer-facing result retrieval",
                "boundary": "GET /api/v1/cad-parse-runs/{id}/summary",
                "module": "backend/app/api/v1/cad_intake.py",
            },
        ],
        "intake": {
            "upload_http_status": upload.status_code,
            "validation_status": payload["validation_status"],
            "parse_status": run["status"],
        },
        "counts": {
            "entities": run["entity_count"],
            "layers": run["layer_count"],
            "blocks": run["block_count"],
            "text_records": run["text_count"],
            "reference_candidates": len(candidates),
            "findings": len(findings),
            "matched_references": matched,
            "missing_references": missing,
            "ambiguous_references": ambiguous,
            "missing_or_ambiguous_references": missing + ambiguous,
            "warning_count": run["warning_count"],
        },
        "entity_types": dict(sorted(entity_types.items())),
        "layers": sorted(
            (
                {
                    "layer_name": layer["layer_name"],
                    "entity_count": layer["entity_count"],
                    "category": layer["review_category"],
                    "requires_human_review": layer["requires_human_review"],
                    "classification_rule": (
                        lambda c: {
                            "rule_kind": c.rule_kind,
                            "confidence": c.confidence,
                            "explanation": c.explanation,
                        }
                    )(layer_taxonomy.classify_layer(layer["layer_name"])),
                }
                for layer in layers
            ),
            key=lambda item: item["layer_name"],
        ),
        "blocks": sorted(
            (
                {
                    "block_name": b["block_name"],
                    "insert_count": b["insert_count"],
                }
                for b in blocks
            ),
            key=lambda item: item["block_name"],
        ),
        "references": sorted(
            (
                {
                    "reference_text": c["reference_text"],
                    "normalized_reference": c["normalized_reference"],
                    "reference_type": c["reference_type"],
                    "match_state": _match_state(c),
                    "confidence_label": c["confidence_label"],
                    "match_reason": c["match_reason"],
                }
                for c in candidates
            ),
            key=lambda item: (
                item["reference_type"],
                item["normalized_reference"],
                item["reference_text"],
            ),
        ),
        "findings": sorted(
            (
                {
                    "finding_type": f["finding_type"],
                    "severity": f["severity"],
                    "title": f["title"],
                    "description": f["description"],
                    "requires_human_review": f["requires_human_review"],
                    "deterministic_rule": True,
                }
                for f in findings
            ),
            key=lambda item: (item["finding_type"], item["title"]),
        ),
        "checks": checks,
        "limitations": expected["known_limitations"],
        "boundary_statement": (
            "This result demonstrates deterministic DXF metadata extraction, "
            "consistency checking, reference identification, and "
            "reviewer-support analysis. It does not verify CAD, validate "
            "design, certify compliance, or approve plans. Every finding "
            "needs human review."
        ),
    }

    return structured, checks


def build_report(structured: dict) -> str:
    counts = structured["counts"]
    lines = [
        "# DXF Integration Test Report",
        "",
        f"Snapshot: {structured['snapshot_id']}",
        "",
        "Synthetic Brookside Meadows subdivision drawing processed through "
        "the real Civil Engineer AI upload, validation, storage, parse, and "
        "retrieval services. The drawing is synthetic review-support data: "
        "conceptual geometry, no survey accuracy, not for construction.",
        "",
        "## Scope statement",
        "",
        structured["boundary_statement"],
        "",
        "## Environment",
        "",
        f"* Parser: {structured['parser']['name']} "
        f"{structured['parser']['version']}",
        "* Backend: FastAPI test client over the production route handlers",
        "* Database: throwaway SQLite seeded with the Brookside Meadows "
        "fixture",
        f"* Drawing units: {structured['drawing_units']} (declared by the "
        "DXF header)",
        "",
        "## Pipeline exercised",
        "",
    ]
    for index, stage in enumerate(structured["pipeline"], start=1):
        lines.append(
            f"{index}. {stage['stage']} ({stage['boundary']}, "
            f"{stage['module']})"
        )
    lines += [
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Upload HTTP status | {structured['intake']['upload_http_status']} |",
        f"| Intake validation | {structured['intake']['validation_status']} |",
        f"| Parse status | {structured['intake']['parse_status']} |",
        f"| Entities | {counts['entities']} |",
        f"| Layers | {counts['layers']} |",
        f"| Blocks | {counts['blocks']} |",
        f"| Text records | {counts['text_records']} |",
        f"| Reference candidates | {counts['reference_candidates']} |",
        f"| Review-support findings | {counts['findings']} |",
        f"| Matched references | {counts['matched_references']} |",
        "| Missing or ambiguous references | "
        f"{counts['missing_or_ambiguous_references']} |",
        "",
        "## Checks",
        "",
        "| Check | Expected | Actual | Result |",
        "| --- | --- | --- | --- |",
    ]
    for check in structured["checks"]:
        outcome = "pass" if check["pass"] else "FAIL"
        lines.append(
            f"| {check['check']} | {check['expected']} | {check['actual']} "
            f"| {outcome} |"
        )
    lines += [
        "",
        "## Known limitations",
        "",
    ]
    for limitation in structured["limitations"]:
        lines.append(f"* {limitation}")
    lines += [
        "",
        "## Reproduce",
        "",
        "```",
        "python scripts/run_dxf_proof.py",
        "```",
        "",
        "The generator (scripts/generate_brookside_proof_dxf.py) and this "
        "harness are deterministic; regenerating produces identical bytes "
        "on the same parser version.",
        "",
    ]
    return "\n".join(lines)


def write_artifacts(structured: dict) -> dict:
    from generate_brookside_proof_dxf import build_dxf_text

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dxf_bytes = build_dxf_text().encode("utf-8")
    result_bytes = (
        json.dumps(structured, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    report_bytes = build_report(structured).encode("utf-8")

    bundle_buffer = io.BytesIO()
    with zipfile.ZipFile(bundle_buffer, "w", zipfile.ZIP_STORED) as bundle:
        for name, data in [
            ("brookside_meadows_realistic_submission.dxf", dxf_bytes),
            ("brookside_meadows_dxf_test_result.json", result_bytes),
            ("DXF_INTEGRATION_TEST_REPORT.md", report_bytes),
            (
                "dxf_proof_expected.json",
                EXPECTED_PATH.read_bytes(),
            ),
        ]:
            info = zipfile.ZipInfo(name, date_time=ZIP_ENTRY_DATE)
            bundle.writestr(info, data)
    bundle_bytes = bundle_buffer.getvalue()

    artifacts = [
        {
            "artifact_id": "proof-dxf",
            "display_name": "Synthetic Brookside Meadows DXF",
            "filename": "brookside_meadows_realistic_submission.dxf",
            "description": (
                "The structurally valid synthetic subdivision drawing: 47 "
                "conceptual lots, road and cul-de-sac alignment, contours, "
                "wetland and buffer, detention and infiltration facilities, "
                "storm pipes, outfall, erosion controls, utilities, sheet "
                "and detail references, and reusable blocks."
            ),
            "file_type": "dxf",
            "content_type": "application/dxf",
            "data": dxf_bytes,
        },
        {
            "artifact_id": "proof-result",
            "display_name": "Structured test result (JSON)",
            "filename": "brookside_meadows_dxf_test_result.json",
            "description": (
                "The structured output of the proof harness: pipeline "
                "stages, extraction counts, layer classifications, "
                "reference states, findings, and every ground-truth check."
            ),
            "file_type": "json",
            "content_type": "application/json; charset=utf-8",
            "data": result_bytes,
        },
        {
            "artifact_id": "proof-report",
            "display_name": "Integration test report (Markdown)",
            "filename": "DXF_INTEGRATION_TEST_REPORT.md",
            "description": (
                "Human-readable report derived from the structured result: "
                "environment, pipeline, metrics, checks, and limitations."
            ),
            "file_type": "markdown",
            "content_type": "text/markdown; charset=utf-8",
            "data": report_bytes,
        },
        {
            "artifact_id": "proof-bundle",
            "display_name": "Complete test bundle (ZIP)",
            "filename": "civil_engineer_dxf_test_bundle.zip",
            "description": (
                "The DXF, structured result, report, and versioned ground "
                "truth in one archive."
            ),
            "file_type": "zip",
            "content_type": "application/zip",
            "data": bundle_bytes,
        },
    ]

    manifest_entries = []
    for artifact in artifacts:
        path = OUTPUT_DIR / artifact["filename"]
        path.write_bytes(artifact["data"])
        manifest_entries.append(
            {
                "artifact_id": artifact["artifact_id"],
                "display_name": artifact["display_name"],
                "filename": artifact["filename"],
                "description": artifact["description"],
                "file_type": artifact["file_type"],
                "content_type": artifact["content_type"],
                "file_size_bytes": len(artifact["data"]),
                "sha256": _sha256(artifact["data"]),
                "snapshot_id": SNAPSHOT_ID,
                "synthetic": True,
                "download_route": (
                    f"/api/proof-of-concept/download/{artifact['artifact_id']}"
                ),
                "related_test_scenario": "scripts/run_dxf_proof.py",
                "source_generator": "scripts/generate_brookside_proof_dxf.py",
            }
        )

    manifest = {
        "snapshot_id": SNAPSHOT_ID,
        "synthetic_disclosure": (
            "All artifacts are generated from a synthetic Brookside Meadows "
            "drawing. Nothing here is a real survey, a real submission, or "
            "an engineering determination."
        ),
        "artifacts": manifest_entries,
    }
    manifest_bytes = (
        json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    (OUTPUT_DIR / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def main() -> int:
    structured, checks = run_harness()
    failed = [c for c in checks if not c["pass"]]
    manifest = write_artifacts(structured)
    print(f"Artifacts written to {OUTPUT_DIR}")
    for entry in manifest["artifacts"]:
        print(
            f"  {entry['filename']} ({entry['file_size_bytes']} bytes, "
            f"sha256 {entry['sha256'][:16]}...)"
        )
    print(f"Checks: {len(checks) - len(failed)} passed, {len(failed)} failed")
    if failed:
        for check in failed:
            print(
                f"  FAIL {check['check']}: expected {check['expected']}, "
                f"actual {check['actual']}"
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
