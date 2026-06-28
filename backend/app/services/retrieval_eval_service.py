"""Lightweight retrieval quality harness for chunk evidence.

Given a project with real-derived chunks and a small labeled query set, this
computes Recall@5, Precision@5, and Mean Reciprocal Rank for the keyword,
semantic, and hybrid retrieval modes, and formats a reproducible Markdown report.

A label marks which page(s) are relevant for a query (by document_id and page
number). Metrics are page-level, matching how a reviewer cites evidence. The
harness measures behavior; it does not assert that one mode must beat another on
every query, and it never makes a determination about document content.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.evidence_retrieval_service import search_project_chunk_evidence

Page = tuple[str, int | None]


def _reciprocal_rank(retrieved: list[Page], relevant: set[Page]) -> float:
    for index, page in enumerate(retrieved):
        if page in relevant:
            return 1.0 / (index + 1)
    return 0.0


def evaluate_modes(
    db: Session,
    project_id: str,
    labeled_queries: list[dict],
    *,
    modes: tuple[str, ...] = ("keyword", "semantic", "hybrid"),
    k: int = 5,
) -> dict:
    """Evaluate retrieval modes over a labeled query set.

    Each labeled query is a dict with keys: query (str), relevant_pages
    (set of (document_id, page_number)), and optional label (str). Returns a
    report dict with per-mode aggregate metrics and per-query detail.
    """

    report: dict = {"project_id": project_id, "k": k, "modes": {}}
    for mode in modes:
        recalls: list[float] = []
        precisions: list[float] = []
        rrs: list[float] = []
        per_query: list[dict] = []
        for item in labeled_queries:
            relevant: set[Page] = set(item["relevant_pages"])
            response = search_project_chunk_evidence(
                db,
                project_id,
                {"query_text": item["query"], "mode": mode, "limit": k},
            )
            retrieved = [
                (r["document_id"], r["page_number"])
                for r in response["results"][:k]
            ]
            hits = [page for page in retrieved if page in relevant]
            recall = (len(set(hits)) / len(relevant)) if relevant else 0.0
            precision = len(hits) / k
            rr = _reciprocal_rank(retrieved, relevant)
            recalls.append(recall)
            precisions.append(precision)
            rrs.append(rr)
            per_query.append(
                {
                    "label": item.get("label", item["query"]),
                    "query": item["query"],
                    "recall_at_k": round(recall, 3),
                    "precision_at_k": round(precision, 3),
                    "reciprocal_rank": round(rr, 3),
                    "result_count": len(response["results"]),
                }
            )

        count = max(len(labeled_queries), 1)
        report["modes"][mode] = {
            "recall_at_k": round(sum(recalls) / count, 3),
            "precision_at_k": round(sum(precisions) / count, 3),
            "mrr": round(sum(rrs) / count, 3),
            "queries": per_query,
        }
    return report


def format_markdown(report: dict) -> str:
    """Format an evaluation report as a Markdown table plus per-query detail."""

    k = report["k"]
    lines: list[str] = []
    lines.append("# Phase 2 Retrieval Quality Report")
    lines.append("")
    lines.append(
        "Measured over a small labeled query set against real-derived chunk "
        "evidence. Scores are relevance measurements for comparing retrieval "
        "modes, not statements about document content."
    )
    lines.append("")
    lines.append(f"| Mode | Recall@{k} | Precision@{k} | MRR |")
    lines.append("| --- | --- | --- | --- |")
    for mode, metrics in report["modes"].items():
        lines.append(
            f"| {mode} | {metrics['recall_at_k']} | "
            f"{metrics['precision_at_k']} | {metrics['mrr']} |"
        )
    lines.append("")
    for mode, metrics in report["modes"].items():
        lines.append(f"## {mode} per-query")
        lines.append("")
        lines.append(f"| Query | Recall@{k} | Precision@{k} | RR |")
        lines.append("| --- | --- | --- | --- |")
        for q in metrics["queries"]:
            lines.append(
                f"| {q['label']} | {q['recall_at_k']} | "
                f"{q['precision_at_k']} | {q['reciprocal_rank']} |"
            )
        lines.append("")
    return "\n".join(lines)
