"""Registration of the background job handlers.

Each handler wraps an existing review-support processor so the worker runs the
exact same logic a reviewer could trigger inline: no processing is duplicated,
only scheduled. Importing this module registers the handlers, so both the API
(when enqueuing) and the worker import it.

Results returned here are non-sensitive JSON summaries only. Domain validation
errors raised by the wrapped services are permanent (a bad input will not
succeed on retry); the worker classifies them so they are not retried.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services import cad_intake_service, job_queue_service, pdf_indexing_service

JOB_PDF_INDEX = "pdf_index"
JOB_CAD_PARSE = "cad_parse"

# Errors that mean the input cannot succeed on retry. The worker fails these
# permanently instead of scheduling a retry.
PERMANENT_ERRORS = (
    pdf_indexing_service.PdfIndexingError,
    cad_intake_service.CadIntakeError,
)


def _pdf_index_handler(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    summary = pdf_indexing_service.index_pdf_document(
        db,
        project_id=payload["project_id"],
        document_id=payload["document_id"],
        **(
            {"actor_name": payload["actor_name"]}
            if payload.get("actor_name")
            else {}
        ),
    )
    indexed_at = summary.get("indexed_at")
    return {
        "document_id": summary.get("document_id"),
        "page_count": summary.get("page_count"),
        "pages_with_text": summary.get("pages_with_text"),
        "pages_without_text": summary.get("pages_without_text"),
        "processing_status": summary.get("processing_status"),
        "text_extraction_status": summary.get("text_extraction_status"),
        "indexed_at": indexed_at.isoformat() if hasattr(indexed_at, "isoformat")
        else indexed_at,
    }


def _cad_parse_handler(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    run = cad_intake_service.parse_dxf_file(db, payload["cad_file_id"])
    # A "failed" run is a normal domain outcome, not a job failure: the run row
    # records the parse result either way.
    return {
        "parse_run_id": run.parse_run_id,
        "cad_file_id": run.cad_file_id,
        "status": run.status,
        "entity_count": run.entity_count,
        "layer_count": run.layer_count,
        "warning_count": run.warning_count,
    }


def register_all() -> None:
    """Register every job handler. Idempotent."""

    job_queue_service.register_handler(JOB_PDF_INDEX, _pdf_index_handler)
    job_queue_service.register_handler(JOB_CAD_PARSE, _cad_parse_handler)


register_all()
