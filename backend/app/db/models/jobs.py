"""Operations bounded context: the durable background processing job queue.

Civil Engineer AI can run file processing (PDF page indexing and DXF metadata
parsing) on a request thread for interactive use, or hand it to a background
worker for large files and higher load. A processing job is a persisted unit of
that deferred work: it survives a restart, records its own lifecycle, retries a
transient failure with backoff, and carries the request correlation id so its
audit trail joins to the request that enqueued it.

Nothing here changes the professional boundary. A job only schedules the same
review-support processing a reviewer could trigger inline; it never approves,
certifies, or validates anything.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    # Handler key, for example "pdf_index" or "cad_parse". Bounded to the
    # registered handlers by the queue service, never free text from a client.
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    # Tenant and project scope for authorization on reads. Stored as an opaque
    # identifier rather than a foreign key so a job row is retained for audit
    # even if its project is later removed.
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    # Non-sensitive job input, for example the document or CAD file id. Never
    # stores file bytes, secrets, or credentials.
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    # queued, running, succeeded, or failed. Managed only by the queue service.
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # When the job becomes eligible to run. Set to the future on a retry so a
    # transient failure backs off instead of spinning.
    available_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    # Worker lease: which worker holds the job and when it was claimed, so a
    # worker that dies mid-job can have its job reclaimed after a timeout.
    locked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Non-sensitive handler result summary on success.
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Safe, client-shown failure reason. Never a stack trace or internal detail.
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Correlation id of the request that enqueued the job, for tracing.
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        # The claim query filters queued jobs that are due, oldest first.
        Index("ix_processing_jobs_claim", "status", "available_at"),
        # Reads are scoped to a project.
        Index("ix_processing_jobs_project", "project_id"),
    )
