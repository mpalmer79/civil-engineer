"""PDF page indexing and evidence citation vocabulary."""

from __future__ import annotations

# Production Foundations Sprint 2 PDF page indexing and evidence citation
# vocabulary. Indexing extracts text from digital PDFs only (no OCR) and is
# deterministic. None of these values implies a final engineering decision,
# approval, certification, compliance state, or that a design is safe.

# Per-page text extraction statuses. no_extractable_text records a page with no
# embedded text layer (for example a scanned image), which is a normal outcome,
# not an error and not a conclusion.
ALLOWED_TEXT_EXTRACTION_STATUSES: set[str] = {
    "not_indexed",
    "indexing_started",
    "text_extracted",
    "no_extractable_text",
    "extraction_failed",
    "unsupported_file_type",
    "needs_reviewer_review",
}

# Document-level processing statuses including Sprint 2 indexing states. These
# track intake and indexing handling only; none implies document approval.
ALLOWED_DOCUMENT_PROCESSING_STATUSES_V2: set[str] = {
    "registered",
    "uploaded",
    "intake_pending",
    "metadata_recorded",
    "indexing_pending",
    "indexing_started",
    "indexed_with_text",
    "indexed_without_text",
    "indexed_with_warnings",
    "indexing_failed",
    "parsing_not_available",
    "needs_reviewer_review",
}

# How an evidence citation was created. reviewer_selected and manual_reference
# are reviewer-driven; extracted_text_reference cites indexed text; there is
# intentionally no verified or approved citation type.
ALLOWED_CITATION_TYPES: set[str] = {
    "reviewer_selected",
    "manual_reference",
    "extracted_text_reference",
    "seeded_demo_reference",
}

# Evidence citation statuses. page_reference_only records a citation to a page
# whose text could not be extracted. extraction_unavailable records that no
# indexed text backs the citation. None implies a final decision; there is
# intentionally no verified or approved citation status.
ALLOWED_CITATION_STATUSES: set[str] = {
    "draft",
    "needs_reviewer_confirmation",
    "reviewer_selected",
    "extraction_unavailable",
    "page_reference_only",
}
