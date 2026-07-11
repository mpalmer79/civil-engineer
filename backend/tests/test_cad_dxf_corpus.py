"""DXF evaluation corpus: generated fixtures with ground-truth expectations.

Each fixture is generated deterministically with ezdxf at test time (no
proprietary drawings are committed), uploaded through the real browser upload
endpoint, parsed through the real parse endpoint, and compared against
expected acceptance status, counts, layer categories, references, facilities,
and findings. The corpus tracks parser compatibility beyond the single
Brookside baseline drawing.
"""

from __future__ import annotations

import io
from pathlib import Path

import ezdxf
import pytest
from fastapi.testclient import TestClient

PROJECT_ID = "proj_brookside_meadows"


def _doc_bytes(doc) -> bytes:
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode("utf-8")


def _upload_and_parse(client: TestClient, name: str, content: bytes) -> dict:
    upload = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files/upload",
        files={"file": (name, content, "application/dxf")},
    )
    assert upload.status_code == 200, upload.text
    payload = upload.json()
    cad_file = payload["cad_file"]
    cad_file["validation_status"] = payload["validation_status"]
    if payload["validation_status"] != "accepted":
        return {"cad_file": cad_file, "run": None}
    parse = client.post(f"/api/v1/cad-files/{cad_file['cad_file_id']}/parse")
    assert parse.status_code == 200, parse.text
    return {"cad_file": cad_file, "run": parse.json()}


def _layers(client: TestClient, run_id: str) -> list[dict]:
    return client.get(f"/api/v1/cad-parse-runs/{run_id}/layers").json()


def _candidates(client: TestClient, run_id: str) -> list[dict]:
    return client.get(
        f"/api/v1/cad-parse-runs/{run_id}/reference-candidates"
    ).json()


def _findings_for_run(client: TestClient, run_id: str) -> list[dict]:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings"
    ).json()
    return [f for f in findings if f["parse_run_id"] == run_id]


def test_corpus_layer_aliases(client: TestClient) -> None:
    """Fixture 2: common civil layer aliases classify without over-flagging."""

    doc = ezdxf.new("R2010")
    layer_expectations = {
        "C-PROP": "property_boundary",
        "C-ROAD": "road_alignment",
        "C-LOTS": "lots_parcels",
        "C-LABEL": "annotation",
        "C-LANDSCAPE": "landscape",
        "C-GRAD": "grading",
        "C-STRM": "stormwater",
        "C-WETL": "wetland_buffer",
        "C-EROS": "erosion_control",
        "C-UTIL": "utilities",
    }
    space = doc.modelspace()
    for index, layer_name in enumerate(layer_expectations):
        doc.layers.add(layer_name)
        space.add_line((index, 0), (index + 1, 1), dxfattribs={"layer": layer_name})

    result = _upload_and_parse(client, "aliases.dxf", _doc_bytes(doc))
    run = result["run"]
    assert run["status"] in {"completed", "completed_with_warnings"}
    layers = {
        layer["layer_name"]: layer["review_category"]
        for layer in _layers(client, run["parse_run_id"])
    }
    for name, expected in layer_expectations.items():
        assert layers[name] == expected, f"{name}: {layers[name]}"
    unknown_findings = [
        f
        for f in _findings_for_run(client, run["parse_run_id"])
        if f["finding_type"] == "unknown_layer_category"
    ]
    assert unknown_findings == []


def test_corpus_minimal_valid_dxf(client: TestClient) -> None:
    """Fixture 3: an empty but valid document parses with zero inventory."""

    doc = ezdxf.new("R2010")
    result = _upload_and_parse(client, "minimal.dxf", _doc_bytes(doc))
    run = result["run"]
    assert run["status"] in {"completed", "completed_with_warnings"}
    assert run["entity_count"] == 0
    assert run["text_count"] == 0


def test_corpus_malformed_dxf(client: TestClient) -> None:
    """Fixture 4: structured-looking garbage is stored for human review."""

    content = b"SECTION garbage that is not a DXF EOF"
    result = _upload_and_parse(client, "malformed.dxf", content)
    cad_file = result["cad_file"]
    if result["run"] is None:
        assert cad_file["validation_status"] == "needs_human_review"
    else:
        assert result["run"]["status"] == "failed"


def test_corpus_unreadable_content_needs_review(client: TestClient) -> None:
    """Fixture 5: content without DXF markers needs human review, no parse."""

    result = _upload_and_parse(client, "noise.dxf", b"not a drawing at all")
    assert result["cad_file"]["validation_status"] == "needs_human_review"
    assert result["run"] is None


def test_corpus_oversized_upload_rejected(client: TestClient) -> None:
    """Fixture 6: a file above the configured limit is rejected before parse."""

    from app.core.config import get_settings

    limit = get_settings().CAD_MAX_UPLOAD_BYTES
    filler = b"0" * (limit + 1)
    upload = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files/upload",
        files={"file": ("big.dxf", filler, "application/dxf")},
    )
    assert upload.status_code in {400, 413, 422}


def test_corpus_excessive_entity_count_truncates(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture 7: entities above the persistence cap truncate gracefully."""

    from app.services import cad_intake_service

    monkeypatch.setattr(cad_intake_service, "MAX_PERSISTED_ENTITIES", 10)
    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    for index in range(25):
        space.add_line((index, 0), (index, 1))
    result = _upload_and_parse(client, "dense.dxf", _doc_bytes(doc))
    run = result["run"]
    assert run["entity_count"] == 25
    truncation = [
        f
        for f in _findings_for_run(client, run["parse_run_id"])
        if "truncated" in f["title"].lower()
    ]
    assert len(truncation) == 1


def test_corpus_nested_rotated_scaled_blocks(client: TestClient) -> None:
    """Fixtures 8 and 9: nested, rotated, and scaled inserts keep bounds."""

    doc = ezdxf.new("R2010")
    inner = doc.blocks.new("INNER_UNIT")
    inner.add_line((0, 0), (1, 1))
    outer = doc.blocks.new("OUTER_UNIT")
    outer.add_blockref("INNER_UNIT", (2, 2))
    space = doc.modelspace()
    space.add_blockref("OUTER_UNIT", (10, 10))
    space.add_blockref(
        "INNER_UNIT", (0, 0), dxfattribs={"rotation": 45, "xscale": 2, "yscale": 2}
    )
    result = _upload_and_parse(client, "blocks.dxf", _doc_bytes(doc))
    run = result["run"]
    assert run["block_count"] == 2
    entities = client.get(
        f"/api/v1/cad-parse-runs/{run['parse_run_id']}/entities"
    ).json()
    inserts = [e for e in entities if e["entity_type"] == "INSERT"]
    assert len(inserts) == 2
    assert all(e["x_min"] is not None for e in inserts)


def test_corpus_model_and_paper_space(client: TestClient) -> None:
    """Fixture 10: paper-space content does not count as model geometry."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    space.add_line((0, 0), (5, 5))
    layout = doc.layout("Layout1")
    layout.add_text("TITLE SHEET C-0.0", dxfattribs={"insert": (1, 1)})
    result = _upload_and_parse(client, "spaces.dxf", _doc_bytes(doc))
    run = result["run"]
    # Only the model-space line is inventoried as an entity.
    assert run["entity_count"] == 1
    assert run["text_count"] == 0


def test_corpus_unicode_labels(client: TestClient) -> None:
    """Fixture 11: unicode text survives extraction."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    space.add_text("滞留池 1 DETENTION BASIN 1", dxfattribs={"insert": (0, 0)})
    result = _upload_and_parse(client, "unicode.dxf", _doc_bytes(doc))
    run = result["run"]
    texts = client.get(
        f"/api/v1/cad-parse-runs/{run['parse_run_id']}/text"
    ).json()
    assert any("滞留池" in t["text_value"] for t in texts)


def test_corpus_reference_scenarios(client: TestClient) -> None:
    """Fixtures 14 to 16: ambiguous, missing, and absent references."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    space.add_text("SEE SHEET C-3.1", dxfattribs={"insert": (0, 0)})
    space.add_text("SEE SHEET C-9.9", dxfattribs={"insert": (0, 2)})
    space.add_text("DETAIL ?/C-4.X", dxfattribs={"insert": (0, 4)})
    result = _upload_and_parse(client, "references.dxf", _doc_bytes(doc))
    run = result["run"]
    candidates = _candidates(client, run["parse_run_id"])
    by_ref = {c["normalized_reference"]: c for c in candidates}
    assert by_ref["C-3.1"]["matched_plan_sheet_id"] is not None
    assert by_ref["C-3.1"]["confidence_label"] == "high"
    assert by_ref["C-9.9"]["matched_plan_sheet_id"] is None
    assert by_ref["C-4.X"]["confidence_label"] == "needs_human_review"
    findings = _findings_for_run(client, run["parse_run_id"])
    types = {f["finding_type"] for f in findings}
    assert "missing_plan_sheet_match" in types
    assert "unclear_detail_reference" in types

    # Fixture 16: no references at all produces no reference candidates.
    quiet = ezdxf.new("R2010")
    quiet.modelspace().add_line((0, 0), (1, 1))
    quiet_result = _upload_and_parse(client, "quiet.dxf", _doc_bytes(quiet))
    assert _candidates(client, quiet_result["run"]["parse_run_id"]) == []


def test_corpus_facility_number_overlap_not_flagged(client: TestClient) -> None:
    """Fixture 18: detention 1 and infiltration 1 are different facilities."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    space.add_text("DETENTION BASIN 1", dxfattribs={"insert": (0, 0)})
    space.add_text("INFILTRATION BASIN 1", dxfattribs={"insert": (200, 200)})
    result = _upload_and_parse(client, "facilities.dxf", _doc_bytes(doc))
    findings = _findings_for_run(client, result["run"]["parse_run_id"])
    conflicts = [
        f for f in findings if f["finding_type"] == "possible_label_conflict"
    ]
    assert conflicts == []


def test_corpus_multiple_facilities_with_real_inconsistency(
    client: TestClient,
) -> None:
    """Fixture 17: a generic label sharing a typed identifier is flagged."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    space.add_text("DETENTION BASIN 2", dxfattribs={"insert": (0, 0)})
    space.add_text("BASIN 2", dxfattribs={"insert": (50, 50)})
    space.add_text("OUTFALL 1", dxfattribs={"insert": (90, 10)})
    result = _upload_and_parse(client, "inconsistent.dxf", _doc_bytes(doc))
    findings = _findings_for_run(client, result["run"]["parse_run_id"])
    conflicts = [
        f for f in findings if f["finding_type"] == "possible_label_conflict"
    ]
    assert len(conflicts) == 1
    assert "needs reviewer confirmation" in conflicts[0]["description"].lower()


def test_corpus_existing_vs_proposed_layers(client: TestClient) -> None:
    """Fixture 19: existing and proposed indicators route correctly."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    for layer_name in ("C-EXST", "C-PROP-ROAD", "C-PROP"):
        doc.layers.add(layer_name)
        space.add_line((0, 0), (1, 1), dxfattribs={"layer": layer_name})
    result = _upload_and_parse(client, "phases.dxf", _doc_bytes(doc))
    layers = {
        layer["layer_name"]: layer["review_category"]
        for layer in _layers(client, result["run"]["parse_run_id"])
    }
    assert layers["C-EXST"] == "existing_conditions"
    assert layers["C-PROP-ROAD"] == "road_alignment"
    assert layers["C-PROP"] == "property_boundary"


def test_corpus_unknown_layer_heavy_drawing(client: TestClient) -> None:
    """Fixture 20: unknown layers stay reviewable at low severity."""

    doc = ezdxf.new("R2010")
    space = doc.modelspace()
    for layer_name in ("X-ALPHA", "X-BRAVO", "X-CHARLIE"):
        doc.layers.add(layer_name)
        space.add_line((0, 0), (1, 1), dxfattribs={"layer": layer_name})
    result = _upload_and_parse(client, "unknowns.dxf", _doc_bytes(doc))
    findings = _findings_for_run(client, result["run"]["parse_run_id"])
    unknown = [
        f for f in findings if f["finding_type"] == "unknown_layer_category"
    ]
    assert len(unknown) == 3
    assert all(f["severity"] == "low" for f in unknown)


def test_corpus_different_units(client: TestClient) -> None:
    """Fixtures 12 and 13: units are read from the header, never assumed."""

    from app.services.cad.geometry import drawing_units

    metric = ezdxf.new("R2010")
    metric.header["$INSUNITS"] = 6
    assert drawing_units(metric).name == "meters"

    imperial = ezdxf.new("R2010")
    imperial.header["$INSUNITS"] = 2
    assert drawing_units(imperial).name == "feet"

    undeclared = ezdxf.new("R2010")
    del undeclared.header["$INSUNITS"]
    units = drawing_units(undeclared)
    assert units.name == "unitless"
    assert units.confidence == "low"


def test_corpus_brookside_baseline_still_passes(client: TestClient) -> None:
    """Fixture 1: the bundled Brookside sample keeps its guarantees."""

    sample = (
        Path(__file__).resolve().parent.parent
        / "app"
        / "cad_samples"
        / "brookside_meadows.dxf"
    )
    result = _upload_and_parse(
        client, "brookside_meadows.dxf", sample.read_bytes()
    )
    run = result["run"]
    assert run["status"] in {"completed", "completed_with_warnings"}
    assert run["entity_count"] > 0
    findings = _findings_for_run(client, run["parse_run_id"])
    types = {f["finding_type"] for f in findings}
    # WET BASIN A and BASIN A remain a possible naming inconsistency, while
    # DETENTION BASIN 1 alone raises nothing.
    assert "possible_label_conflict" in types
    conflict = next(
        f for f in findings if f["finding_type"] == "possible_label_conflict"
    )
    assert "BASIN A" in conflict["description"]
    assert "DETENTION BASIN 1" not in conflict["description"]
