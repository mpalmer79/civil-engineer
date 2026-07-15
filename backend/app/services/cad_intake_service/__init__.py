"""Real CAD (DXF) intake and parsing service.

This service registers a real DXF file, parses it with the ezdxf library, and
extracts review-support metadata: layers, entities, blocks, text, reference
candidates, and review-support findings. It compares extracted sheet and detail
references against the seeded Phase 6 plan sheets and raises review-support
findings when a reference has no match, a detail reference is ambiguous, a basin
label may conflict, or a layer cannot be categorized.

Phase 12 adds browser DXF upload, intake validation, a manual parse queue, a CAD
intake dashboard, and promotion of selected CAD findings into the workflow board.
Uploaded files are validated (extension, size, content type, readability), stored
under a safe generated file name (never the raw user file name), and registered
as a CAD file. Parse is triggered manually; there is no background worker.

Parsing extracts metadata from a real DXF file. It does not verify CAD, validate
geometry or design, certify compliance, or make final engineering decisions. DXF
is the only supported file type in this phase; DWG parsing is out of scope. There
is no action called approve. A parse queue status of "failed" means the parser
could not read the file (a technical parse failure), not an engineering failure.

Read side effects: get_cad_parse_summary, list_cad_layers, list_cad_text,
get_cad_file_review_context, get_cad_parse_queue, get_cad_intake_dashboard, and
list_unpromoted_cad_findings each write an audit event recording the access. This
is intentional so the decision history shows reviewer access.

This module is a package. The implementation is split by responsibility across
errors, uploads, parsing, findings, insights, and reads submodules. Every public
name is re-exported here so the import path is unchanged: callers continue to use
``from app.services import cad_intake_service`` and
``from app.services.cad_intake_service import <name>``.
"""

from __future__ import annotations

from app.services.cad_intake_service.errors import (
    CONTEXT_NOTE,
    LIMITATIONS_NOTE,
    PARSER_NAME,
    PARSER_VERSION,
    CadIntakeError,
)
from app.services.cad_intake_service.findings import (
    create_workflow_items_from_cad_findings,
    promote_cad_finding_to_workflow,
    promote_selected_cad_findings_to_workflow,
)
from app.services.cad_intake_service.insights import (
    compare_cad_references_to_plan_sheets,
    get_cad_file_review_context,
    get_cad_intake_dashboard,
    get_cad_parse_queue,
    get_cad_parse_summary,
)
from app.services.cad_intake_service.parsing import (
    MAX_LAYER_COUNT,
    MAX_PERSISTED_ENTITIES,
    MAX_TEXT_VALUE_LENGTH,
    OUTFALL_RE,
    PIPE_RE,
    ensure_cad_intake,
    parse_dxf_file,
    request_cad_parse,
)
from app.services.cad_intake_service.references import NEUTRAL_LAYERS
from app.services.cad_intake_service.reads import (
    get_cad_file,
    get_cad_parse_run,
    list_cad_blocks,
    list_cad_entities,
    list_cad_files,
    list_cad_layers,
    list_cad_parse_runs,
    list_cad_reference_candidates,
    list_cad_review_findings,
    list_cad_text,
    list_unpromoted_cad_findings,
)
from app.services.cad_intake_service.uploads import (
    ALLOWED_UPLOAD_CONTENT_TYPES,
    DXF_CONTENT_TYPES,
    GENERIC_CONTENT_TYPES,
    SAMPLE_DIR,
    SAMPLE_DXF_FILES,
    SUPPORTED_UPLOAD_EXTENSIONS,
    create_cad_file_from_sample,
    create_cad_file_from_upload,
    create_cad_file_upload,
    get_cad_upload_limits,
    save_uploaded_dxf_file,
    validate_cad_upload_file,
)

__all__ = [
    "ALLOWED_UPLOAD_CONTENT_TYPES",
    "CONTEXT_NOTE",
    "CadIntakeError",
    "DXF_CONTENT_TYPES",
    "GENERIC_CONTENT_TYPES",
    "LIMITATIONS_NOTE",
    "MAX_LAYER_COUNT",
    "MAX_PERSISTED_ENTITIES",
    "MAX_TEXT_VALUE_LENGTH",
    "NEUTRAL_LAYERS",
    "OUTFALL_RE",
    "PARSER_NAME",
    "PARSER_VERSION",
    "PIPE_RE",
    "SAMPLE_DIR",
    "SAMPLE_DXF_FILES",
    "SUPPORTED_UPLOAD_EXTENSIONS",
    "compare_cad_references_to_plan_sheets",
    "create_cad_file_from_sample",
    "create_cad_file_from_upload",
    "create_cad_file_upload",
    "create_workflow_items_from_cad_findings",
    "ensure_cad_intake",
    "get_cad_file",
    "get_cad_file_review_context",
    "get_cad_intake_dashboard",
    "get_cad_parse_queue",
    "get_cad_parse_run",
    "get_cad_parse_summary",
    "get_cad_upload_limits",
    "list_cad_blocks",
    "list_cad_entities",
    "list_cad_files",
    "list_cad_layers",
    "list_cad_parse_runs",
    "list_cad_reference_candidates",
    "list_cad_review_findings",
    "list_cad_text",
    "list_unpromoted_cad_findings",
    "parse_dxf_file",
    "promote_cad_finding_to_workflow",
    "promote_selected_cad_findings_to_workflow",
    "request_cad_parse",
    "save_uploaded_dxf_file",
    "validate_cad_upload_file",
]
