"""PDF page indexing and reviewer evidence citation service.

Production Foundations Sprint 2 adds the first document-understanding layer for
uploaded PDF files. It indexes a real uploaded PDF into page-level review
records, extracts embedded text where the PDF carries a text layer, and lets a
human reviewer cite an exact page or section as evidence for a review-support
finding.

Indexing is deterministic and local. It reads the uploaded file with pypdf, does
not OCR scanned pages, and never sends document content to any AI provider.
Nothing here approves plans, certifies compliance, verifies CAD, validates
design, declares a project safe, resolves or closes an issue, or makes a final
engineering decision. A citation is a reviewer-selected source reference, not
proof of correctness, and it never changes a finding to a final outcome.

Audit metadata records counts and statuses only. Extracted page text and raw
server file paths are never written to audit events or user-facing summaries.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CITATION_STATUSES,
    ALLOWED_CITATION_TYPES,
    reject_prohibited_language,
)
from app.db import models
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)

PDF_EXTRACTION_METHOD = "pypdf_text_layer"


class PdfIndexingError(Exception):
    """Raised when a PDF indexing or citation operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise PdfIndexingError("Project not found.", status_code=404)
    return project


def _require_document(
    db: Session, project_id: str, document_id: str
) -> models.Document:
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise PdfIndexingError("Document not found.", status_code=404)
    return document


def _looks_like_pdf(document: models.Document) -> bool:
    name = (document.original_file_name or document.file_name or "").lower()
    if name.endswith(".pdf"):
        return True
    return (document.content_type or "").lower() == "application/pdf"


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def index_pdf_document(
    db: Session,
    *,
    project_id: str,
    document_id: str,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Index an uploaded PDF into page records and extract embedded text.

    Returns an indexing summary (counts and statuses only). Raises
    PdfIndexingError when the document is not a PDF, has no uploaded file, the
    file is missing, or the file cannot be opened at all.
    """

    _require_project(db, project_id)
    document = _require_document(db, project_id, document_id)
    ensure_demo_actor(db)

    if not _looks_like_pdf(document):
        raise PdfIndexingError(
            "PDF indexing requires a PDF document. This document is not a PDF.",
            status_code=422,
        )
    if not document.storage_path:
        raise PdfIndexingError(
            "PDF indexing requires an uploaded PDF file. Register is not enough; "
            "upload the file first.",
            status_code=422,
        )
    storage_path = Path(document.storage_path)
    if not storage_path.is_file():
        raise PdfIndexingError(
            "The uploaded file could not be found for indexing.",
            status_code=422,
        )

    document.processing_status = "indexing_started"
    document.text_extraction_status = "indexing_started"
    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_indexing_started",
        related_entity_type="document",
        related_entity_id=document_id,
        description=f"Reviewer started PDF indexing for '{document.original_file_name or document.file_name}'.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={"document_id": document_id},
    )
    db.commit()

    try:
        reader = PdfReader(str(storage_path))
        total_pages = len(reader.pages)
    except Exception as exc:  # noqa: BLE001 - any pypdf failure is a safe failure
        document.processing_status = "indexing_failed"
        document.text_extraction_status = "extraction_failed"
        document.text_extraction_summary = (
            "The PDF could not be opened for indexing."
        )
        record_audit_event(
            db,
            project_id=project_id,
            event_type="document_indexing_failed",
            related_entity_type="document",
            related_entity_id=document_id,
            description="PDF indexing failed: the file could not be opened.",
            actor_type="reviewer",
            actor_display_name=actor_name,
            metadata={"document_id": document_id, "reason": "unreadable_pdf"},
        )
        db.commit()
        raise PdfIndexingError(
            "The uploaded PDF could not be opened. It may be malformed or "
            "encrypted. A reviewer should check the file.",
            status_code=422,
        ) from exc

    pages_with_text = 0
    pages_without_text = 0
    warning_count = 0

    for index in range(total_pages):
        page_number = index + 1
        warnings: list[str] = []
        text: str | None = None
        try:
            text = reader.pages[index].extract_text()
        except Exception:  # noqa: BLE001 - one bad page must not stop the rest
            warnings.append("Text extraction failed for this page.")

        if text and text.strip():
            normalized = text.strip()
            status = "text_extracted"
            method = PDF_EXTRACTION_METHOD
            char_count = len(normalized)
            word_count = _word_count(normalized)
            pages_with_text += 1
        else:
            normalized = None
            status = "no_extractable_text"
            method = None
            char_count = 0
            word_count = 0
            pages_without_text += 1
        if warnings:
            warning_count += 1

        _upsert_page(
            db,
            project_id=project_id,
            document_id=document_id,
            page_number=page_number,
            extracted_text=normalized,
            text_extraction_status=status,
            text_extraction_method=method,
            char_count=char_count,
            word_count=word_count,
            extraction_warnings=warnings,
        )

        record_audit_event(
            db,
            project_id=project_id,
            event_type=(
                "document_page_text_extracted"
                if status == "text_extracted"
                else "document_page_no_extractable_text"
            ),
            related_entity_type="document_page",
            related_entity_id=f"{document_id}#p{page_number}",
            description=(
                f"Page {page_number}: {status.replace('_', ' ')}."
            ),
            actor_type="system",
            actor_id=DEMO_ACTOR_ID,
            actor_display_name=actor_name,
            metadata={
                "document_id": document_id,
                "page_number": page_number,
                "char_count": char_count,
                "word_count": word_count,
                "warning_count": len(warnings),
            },
        )

    now = _now()
    if warning_count > 0:
        processing_status = "indexed_with_warnings"
    elif pages_with_text > 0:
        processing_status = "indexed_with_text"
    else:
        processing_status = "indexed_without_text"

    document.page_count = total_pages
    document.indexed_at = now
    document.processing_status = processing_status
    document.text_extraction_status = (
        "text_extracted" if pages_with_text > 0 else "no_extractable_text"
    )
    document.extraction_warning_count = warning_count
    summary_text = (
        f"{total_pages} page(s) indexed: {pages_with_text} with extractable "
        f"text, {pages_without_text} without. {warning_count} page warning(s)."
    )
    document.text_extraction_summary = summary_text

    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_indexed",
        related_entity_type="document",
        related_entity_id=document_id,
        description=f"PDF indexed: {summary_text}",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "document_id": document_id,
            "page_count": total_pages,
            "pages_with_text": pages_with_text,
            "pages_without_text": pages_without_text,
            "warning_count": warning_count,
            "processing_status": processing_status,
        },
    )
    db.commit()

    return {
        "document_id": document_id,
        "page_count": total_pages,
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "warning_count": warning_count,
        "processing_status": processing_status,
        "text_extraction_status": document.text_extraction_status,
        "indexed_at": now,
        "summary": summary_text,
    }


def _upsert_page(
    db: Session,
    *,
    project_id: str,
    document_id: str,
    page_number: int,
    extracted_text: str | None,
    text_extraction_status: str,
    text_extraction_method: str | None,
    char_count: int,
    word_count: int,
    extraction_warnings: list[str],
) -> models.DocumentPage:
    """Create or update a DocumentPage so re-indexing is idempotent."""

    existing = db.scalars(
        select(models.DocumentPage).where(
            models.DocumentPage.document_id == document_id,
            models.DocumentPage.page_number == page_number,
        )
    ).first()
    now = _now()
    if existing is None:
        page = models.DocumentPage(
            document_page_id=f"docpage_{_short()}",
            project_id=project_id,
            document_id=document_id,
            page_number=page_number,
            page_label=f"Page {page_number}",
            extracted_text=extracted_text,
            text_extraction_status=text_extraction_status,
            text_extraction_method=text_extraction_method,
            char_count=char_count,
            word_count=word_count,
            extraction_warnings=extraction_warnings,
            indexed_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(page)
        return page

    existing.extracted_text = extracted_text
    existing.text_extraction_status = text_extraction_status
    existing.text_extraction_method = text_extraction_method
    existing.char_count = char_count
    existing.word_count = word_count
    existing.extraction_warnings = extraction_warnings
    existing.indexed_at = now
    existing.updated_at = now
    return existing


def list_document_pages(
    db: Session, project_id: str, document_id: str
) -> list[models.DocumentPage]:
    _require_document(db, project_id, document_id)
    stmt = (
        select(models.DocumentPage)
        .where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.document_id == document_id,
        )
        .order_by(models.DocumentPage.page_number)
    )
    return list(db.scalars(stmt).all())


def get_document_page(
    db: Session, project_id: str, document_id: str, page_number: int
) -> models.DocumentPage | None:
    _require_document(db, project_id, document_id)
    return db.scalars(
        select(models.DocumentPage).where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.document_id == document_id,
            models.DocumentPage.page_number == page_number,
        )
    ).first()


# ---------------------------------------------------------------------------
# Evidence citations
# ---------------------------------------------------------------------------


def create_evidence_citation(
    db: Session,
    *,
    project_id: str,
    finding_id: str,
    document_id: str,
    document_page_id: str | None = None,
    page_number: int | None = None,
    section_label: str | None = None,
    quoted_excerpt: str | None = None,
    reviewer_note: str | None = None,
    citation_type: str = "reviewer_selected",
    citation_status: str | None = None,
    created_by_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCitation:
    """Create a reviewer-selected, page-level evidence citation for a finding."""

    _require_project(db, project_id)
    finding = db.get(models.Finding, finding_id)
    if finding is None or finding.project_id != project_id:
        raise PdfIndexingError("Finding not found.", status_code=404)
    document = _require_document(db, project_id, document_id)
    ensure_demo_actor(db)

    for field, value in (
        ("section_label", section_label),
        ("quoted_excerpt", quoted_excerpt),
        ("reviewer_note", reviewer_note),
    ):
        reject_prohibited_language(value, field=field)

    if citation_type not in ALLOWED_CITATION_TYPES:
        raise PdfIndexingError(
            f"Invalid citation_type '{citation_type}'.", status_code=422
        )

    page: models.DocumentPage | None = None
    if document_page_id:
        page = db.get(models.DocumentPage, document_page_id)
        if page is None or page.document_id != document_id:
            raise PdfIndexingError(
                "Document page not found for this document.", status_code=422
            )
    elif page_number is not None:
        page = db.scalars(
            select(models.DocumentPage).where(
                models.DocumentPage.document_id == document_id,
                models.DocumentPage.page_number == page_number,
            )
        ).first()

    resolved_page_number = page.page_number if page else page_number
    resolved_page_label = page.page_label if page else None

    # Choose a safe default status. A citation to a page with no extractable
    # text is recorded as page_reference_only; a citation with no resolved page
    # is extraction_unavailable; otherwise it needs reviewer confirmation.
    if citation_status is None:
        if page is not None and page.text_extraction_status == "no_extractable_text":
            citation_status = "page_reference_only"
        elif page is None and resolved_page_number is None:
            citation_status = "extraction_unavailable"
        else:
            citation_status = "needs_reviewer_confirmation"
    if citation_status not in ALLOWED_CITATION_STATUSES:
        raise PdfIndexingError(
            f"Invalid citation_status '{citation_status}'.", status_code=422
        )

    now = _now()
    citation = models.EvidenceCitation(
        evidence_citation_id=f"cite_{_short()}",
        project_id=project_id,
        finding_id=finding_id,
        document_id=document_id,
        document_page_id=page.document_page_id if page else None,
        page_number=resolved_page_number,
        page_label=resolved_page_label,
        section_label=section_label,
        quoted_excerpt=quoted_excerpt,
        reviewer_note=reviewer_note,
        citation_type=citation_type,
        citation_status=citation_status,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=created_by_name,
        source_mode="user_created",
        created_at=now,
        updated_at=now,
    )
    db.add(citation)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_citation_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer cited '{document.original_file_name or document.file_name}'"
            + (
                f" page {resolved_page_number}"
                if resolved_page_number is not None
                else ""
            )
            + f" as evidence for finding '{finding.title}'."
        ),
        actor_type="reviewer",
        actor_display_name=created_by_name,
        metadata={
            "evidence_citation_id": citation.evidence_citation_id,
            "document_id": document_id,
            "page_number": resolved_page_number,
            "citation_type": citation_type,
            "citation_status": citation_status,
        },
    )
    db.commit()
    db.refresh(citation)
    return citation


def list_finding_citations(
    db: Session, project_id: str, finding_id: str
) -> list[models.EvidenceCitation]:
    stmt = (
        select(models.EvidenceCitation)
        .where(
            models.EvidenceCitation.project_id == project_id,
            models.EvidenceCitation.finding_id == finding_id,
        )
        .order_by(models.EvidenceCitation.created_at)
    )
    return list(db.scalars(stmt).all())


def list_project_citations(
    db: Session, project_id: str
) -> list[models.EvidenceCitation]:
    stmt = (
        select(models.EvidenceCitation)
        .where(models.EvidenceCitation.project_id == project_id)
        .order_by(models.EvidenceCitation.created_at)
    )
    return list(db.scalars(stmt).all())


def count_finding_citations(db: Session, project_id: str) -> dict[str, int]:
    """Return a map of finding_id to citation count for a project."""

    counts: dict[str, int] = {}
    for citation in list_project_citations(db, project_id):
        counts[citation.finding_id] = counts.get(citation.finding_id, 0) + 1
    return counts


def update_evidence_citation(
    db: Session,
    *,
    project_id: str,
    finding_id: str,
    citation_id: str,
    section_label: str | None = None,
    quoted_excerpt: str | None = None,
    reviewer_note: str | None = None,
    citation_status: str | None = None,
    citation_type: str | None = None,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCitation:
    citation = db.get(models.EvidenceCitation, citation_id)
    if (
        citation is None
        or citation.project_id != project_id
        or citation.finding_id != finding_id
    ):
        raise PdfIndexingError("Citation not found.", status_code=404)

    for field, value in (
        ("section_label", section_label),
        ("quoted_excerpt", quoted_excerpt),
        ("reviewer_note", reviewer_note),
    ):
        reject_prohibited_language(value, field=field)

    if section_label is not None:
        citation.section_label = section_label
    if quoted_excerpt is not None:
        citation.quoted_excerpt = quoted_excerpt
    if reviewer_note is not None:
        citation.reviewer_note = reviewer_note
    if citation_status is not None:
        if citation_status not in ALLOWED_CITATION_STATUSES:
            raise PdfIndexingError(
                f"Invalid citation_status '{citation_status}'.",
                status_code=422,
            )
        citation.citation_status = citation_status
    if citation_type is not None:
        if citation_type not in ALLOWED_CITATION_TYPES:
            raise PdfIndexingError(
                f"Invalid citation_type '{citation_type}'.", status_code=422
            )
        citation.citation_type = citation_type
    citation.updated_at = _now()

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_citation_updated",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=f"Reviewer updated evidence citation {citation_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "evidence_citation_id": citation_id,
            "citation_status": citation.citation_status,
        },
    )
    db.commit()
    db.refresh(citation)
    return citation


def delete_evidence_citation(
    db: Session,
    *,
    project_id: str,
    finding_id: str,
    citation_id: str,
    actor_name: str = DEMO_ACTOR_NAME,
) -> None:
    citation = db.get(models.EvidenceCitation, citation_id)
    if (
        citation is None
        or citation.project_id != project_id
        or citation.finding_id != finding_id
    ):
        raise PdfIndexingError("Citation not found.", status_code=404)
    db.delete(citation)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_citation_removed",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=f"Reviewer removed evidence citation {citation_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={"evidence_citation_id": citation_id},
    )
    db.commit()
