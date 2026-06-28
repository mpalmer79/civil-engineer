"""Retrieval quality harness test with a small labeled query set.

Builds a controlled corpus, evaluates keyword, semantic, and hybrid retrieval,
and asserts conservative thresholds that catch major regressions without being
brittle. Set CIVIL_WRITE_RETRIEVAL_REPORT=1 to also write the Markdown report to
docs/PHASE_2_RETRIEVAL_QUALITY.md (used to regenerate the committed report).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.services import retrieval_eval_service

from tests.test_chunk_evidence_retrieval import (
    _create_project,
    _index,
    _chunk,
    _make_pdf,
    _upload_pdf,
)
from tests.test_chunk_scoped_retrieval import _embed

_PAGES = [
    "Detention basin outlet structure sizing and discharge control design.",
    "Infiltration basin drawdown time and percolation rate analysis.",
    "Erosion and sediment control during construction with silt fence.",
    "Culvert capacity and stormwater drainage conveyance design.",
]


def _labeled_queries(document_id: str) -> list[dict]:
    return [
        {
            "label": "exact: detention basin outlet",
            "query": "detention basin outlet",
            "relevant_pages": {(document_id, 1)},
        },
        {
            "label": "semantic: retention pond",
            "query": "retention pond",
            "relevant_pages": {(document_id, 1)},
        },
        {
            "label": "exact: infiltration drawdown",
            "query": "infiltration drawdown",
            "relevant_pages": {(document_id, 2)},
        },
        {
            "label": "semantic: groundwater recharge",
            "query": "groundwater recharge",
            "relevant_pages": {(document_id, 2)},
        },
        {
            "label": "exact: silt fence erosion",
            "query": "silt fence erosion",
            "relevant_pages": {(document_id, 3)},
        },
        {
            "label": "exact: culvert capacity",
            "query": "culvert capacity",
            "relevant_pages": {(document_id, 4)},
        },
    ]


def test_retrieval_quality_harness(client: TestClient) -> None:
    pid = _create_project(client, "Retrieval Quality Project")
    did = _upload_pdf(client, pid, _make_pdf(_PAGES))
    _index(client, pid, did)
    _chunk(client, pid, did)
    _embed(client, pid)

    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        report = retrieval_eval_service.evaluate_modes(
            db, pid, _labeled_queries(did)
        )
    finally:
        db.close()

    keyword = report["modes"]["keyword"]
    semantic = report["modes"]["semantic"]
    hybrid = report["modes"]["hybrid"]

    # Conservative, non-brittle guards.
    # Keyword finds the exact-match queries.
    assert keyword["recall_at_k"] >= 0.5
    # Semantic surfaces at least some relevant pages (including synonym queries).
    assert semantic["recall_at_k"] > 0.0
    # Hybrid combines both, so it is at least as good as keyword on recall.
    assert hybrid["recall_at_k"] >= keyword["recall_at_k"] - 1e-9
    # Metrics are well-formed.
    for metrics in (keyword, semantic, hybrid):
        assert 0.0 <= metrics["recall_at_k"] <= 1.0
        assert 0.0 <= metrics["precision_at_k"] <= 1.0
        assert 0.0 <= metrics["mrr"] <= 1.0

    markdown = retrieval_eval_service.format_markdown(report)
    assert "Retrieval Quality Report" in markdown
    assert "hybrid" in markdown

    if os.environ.get("CIVIL_WRITE_RETRIEVAL_REPORT") == "1":
        out = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "PHASE_2_RETRIEVAL_QUALITY.md"
        )
        out.write_text(markdown + "\n", encoding="utf-8")
