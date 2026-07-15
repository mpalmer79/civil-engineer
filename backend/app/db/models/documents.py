"""Documents bounded context: uploaded documents, indexed pages, chunks, embeddings, and hotspots."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_information: Mapped[str] = mapped_column(Text, nullable=False)
    intentionally_missing_or_conflicting_information: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )

    # Production foundation fields (Sprint 1). Nullable with safe defaults so the
    # seeded demo documents keep working. source_mode distinguishes seeded demo
    # documents from user-registered or user-uploaded documents. processing_status
    # never implies document approval; it tracks intake handling only.
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    original_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_status: Mapped[str | None] = mapped_column(String, nullable=True)
    processing_status: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    revision_label: Mapped[str | None] = mapped_column(String, nullable=True)
    revision_date: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    is_superseded: Mapped[bool] = mapped_column(default=False)
    superseded_by_document_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Production foundation fields (Sprint 6) for durable storage. Nullable with
    # safe defaults so seeded and Sprint 1 through 5 documents keep working.
    # storage_path is retained above for backward compatibility; new code uses
    # storage_key and storage_provider. None of these implies document approval.
    storage_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_bucket: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_etag: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_version_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    file_available: Mapped[bool] = mapped_column(default=False)
    last_storage_check_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Production foundation fields (Sprint 2) for PDF page indexing. Nullable
    # with safe defaults so seeded and Sprint 1 documents keep working. These
    # track digital PDF text extraction state only; none implies approval.
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    text_extraction_status: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    text_extraction_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    extraction_warning_count: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="documents")
    pages: Mapped[list["DocumentPage"]] = relationship(back_populates="document")


class DocumentPage(Base):
    """A page-level review record produced by indexing an uploaded PDF.

    Production Foundations Sprint 2 indexes uploaded digital PDFs into page
    records and extracts text where the PDF carries an embedded text layer.
    Indexing reads a real uploaded file deterministically with pypdf. It does
    not OCR scanned pages, send content to any AI provider, approve plans,
    certify compliance, verify CAD, validate design, or make any final
    engineering decision. A page with no embedded text is recorded as
    no_extractable_text, not an error and not a conclusion.
    """

    __tablename__ = "document_pages"

    document_page_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_label: Mapped[str | None] = mapped_column(String, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_extraction_status: Mapped[str] = mapped_column(
        String, default="not_indexed"
    )
    text_extraction_method: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    extraction_warnings: Mapped[list] = mapped_column(JSON, default=list)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    document: Mapped["Document"] = relationship(back_populates="pages")


class DocumentChunk(Base):
    """A short, retrievable excerpt of source evidence from a document.

    Phase 3 seeds synthetic chunks rather than parsing real documents. Each
    chunk carries enough metadata (page, section, keywords, related checklist
    items and findings) to support keyword and metadata based retrieval.

    Provenance: chunk_origin records whether a chunk is seeded demo data
    (seeded_demo) or built from indexed PDF page text (real_derived). Older rows
    created before this column existed may have a null chunk_origin; for those,
    real-derived status falls back to the chunk_id prefix
    (page_chunking_service.REAL_DERIVED_CHUNK_PREFIX). New code should write and
    prefer chunk_origin.

    Migration note: this repo initializes schema with Base.metadata.create_all
    and has no migration tooling, so adding this column applies automatically to
    fresh databases only. An existing production database needs a one-time
    ALTER TABLE (or a backfill) to add and populate chunk_origin. See
    docs/archive/PHASE_1_REAL_PDF_INDEXING_AUDIT.md.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[str | None] = mapped_column(String, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    # Durable provenance. Nullable so older rows (created before this column)
    # keep working; those fall back to the chunk_id prefix for real-derived
    # detection. New rows are written with an explicit value.
    chunk_origin: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ChunkEmbedding(Base):
    """A deterministic, locally computed embedding vector for a document chunk.

    Embeddings power semantic and hybrid retrieval over real-derived chunks. The
    vector is stored as JSON (a portable, dependency-free fallback). For larger
    datasets a pgvector column should replace this JSON storage; see
    docs/archive/PHASE_2_RETRIEVAL_BRAIN.md. The provider, model name, and model version
    are recorded so a stored vector can be detected as stale and re-embedded when
    the embedding model changes. content_hash detects chunk content changes.
    No provider secrets are ever stored here.
    """

    __tablename__ = "chunk_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("document_chunks.chunk_id"), unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector: Mapped[list] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    civil_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_planted_issues: Mapped[list] = mapped_column(JSON, default=list)
    future_drilldown: Mapped[str] = mapped_column(Text, nullable=False)
    position_x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    position_y_percent: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="hotspots")
