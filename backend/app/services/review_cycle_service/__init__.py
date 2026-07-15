"""Phase 13 multi-round resubmittal, revision comparison, and response cycle.

This service tracks multiple review rounds for a project. A reviewer can create
or load a review cycle, record a resubmittal package, link uploaded DXF files and
applicant responses, compare the current DXF parse metadata against a previous
round, map applicant responses to prior response package or workflow items, mark
review-support resolution statuses, carry unresolved items forward, and prepare
the next review cycle.

Everything here is review-support and evidence-organization. It does not approve
plans, certify compliance, stamp drawings, verify CAD, validate design, or make
final engineering decisions. Revision comparison compares extracted DXF metadata
(layers, references, blocks, and review findings) only; it never compares geometry
in a way that implies engineering validation, and there is no action called
approve. Resolution statuses such as addressed_for_review are review-support
states, never final decisions like resolved, closed, approved, or certified.

Read side effects: get_review_cycle, get_review_cycle_dashboard,
get_revision_comparison_run, list_revision_change_records, get_response_mapping_summary,
get_carry_forward_summary, get_resolution_summary, and get_next_cycle_preparation
each write an audit event recording reviewer access. This is intentional so the
decision history shows reviewer access.

This package splits the service into cohesive submodules (errors, lifecycle,
resubmittals, responses, comparison, carry_forward, dashboard) and re-exports the
full public surface so both import styles keep working unchanged:

    from app.services import review_cycle_service
    from app.services.review_cycle_service import create_review_cycle

Behavior, signatures, transaction and commit calls, and public names are
unchanged by the split.
"""

from __future__ import annotations

from app.core.safety import (
    ALLOWED_APPLICANT_RESPONSE_STATUSES,
    ALLOWED_CARRY_FORWARD_STATUSES,
    ALLOWED_MAPPING_CONFIDENCE_LABELS,
    ALLOWED_NEXT_CYCLE_STATUSES,
    ALLOWED_RESOLUTION_STATUSES,
    ALLOWED_RESUBMITTAL_STATUSES,
    ALLOWED_REVIEW_CYCLE_STATUSES,
    ALLOWED_REVISION_COMPARISON_STATUSES,
)

from app.services.review_cycle_service._common import (
    _STOPWORDS,
    _audit,
    _keywords,
    _latest_response_package,
    _now,
    _require_project,
    _response_package_items,
    _short,
    _stem,
)
from app.services.review_cycle_service.errors import (
    FINDING_TYPE_TO_CATEGORY,
    LIMITATIONS_NOTE,
    REF_TYPE_TO_CATEGORY,
    STEM_CATEGORIES,
    ReviewCycleError,
)
from app.services.review_cycle_service.lifecycle import (
    _active_cycle,
    _require_cycle,
    create_review_cycle,
    ensure_review_cycle,
    get_review_cycle,
    get_review_cycle_record,
    get_review_cycle_summary,
    list_review_cycles,
)
from app.services.review_cycle_service.resubmittals import (
    create_resubmittal_package,
    get_resubmittal_package,
    get_resubmittal_package_record,
    link_applicant_response_to_resubmittal,
    link_cad_file_to_resubmittal,
    list_resubmittal_documents,
    list_resubmittal_packages,
    update_resubmittal_package_status,
)
from app.services.review_cycle_service.responses import (
    _get_applicant_response,
    auto_suggest_response_mappings,
    create_applicant_response_mapping,
    get_response_mapping_summary,
    list_applicant_responses,
    list_response_mappings_for_cycle,
)
from app.services.review_cycle_service.comparison import (
    _change_severity,
    _findings_for_run,
    _round_metadata,
    get_revision_comparison_run,
    get_revision_comparison_run_record,
    list_revision_change_records,
    list_revision_comparison_runs,
    run_revision_comparison,
    summarize_revision_changes,
)
from app.services.review_cycle_service.carry_forward import (
    _add_carry_forward,
    _existing_carry_forward_sources,
    carry_forward_unresolved_items,
    create_issue_carry_forward,
    create_response_resolution_record,
    get_carry_forward_summary,
    get_next_cycle_preparation,
    get_resolution_summary,
    list_issue_carry_forwards,
    list_response_resolution_records,
    prepare_next_cycle,
    update_response_resolution_status,
)
from app.services.review_cycle_service.dashboard import (
    get_review_cycle_dashboard,
)

__all__ = [
    "ALLOWED_APPLICANT_RESPONSE_STATUSES",
    "ALLOWED_CARRY_FORWARD_STATUSES",
    "ALLOWED_MAPPING_CONFIDENCE_LABELS",
    "ALLOWED_NEXT_CYCLE_STATUSES",
    "ALLOWED_RESOLUTION_STATUSES",
    "ALLOWED_RESUBMITTAL_STATUSES",
    "ALLOWED_REVIEW_CYCLE_STATUSES",
    "ALLOWED_REVISION_COMPARISON_STATUSES",
    "FINDING_TYPE_TO_CATEGORY",
    "LIMITATIONS_NOTE",
    "REF_TYPE_TO_CATEGORY",
    "STEM_CATEGORIES",
    "ReviewCycleError",
    "auto_suggest_response_mappings",
    "carry_forward_unresolved_items",
    "create_applicant_response_mapping",
    "create_issue_carry_forward",
    "create_response_resolution_record",
    "create_resubmittal_package",
    "create_review_cycle",
    "ensure_review_cycle",
    "get_carry_forward_summary",
    "get_next_cycle_preparation",
    "get_resolution_summary",
    "get_response_mapping_summary",
    "get_resubmittal_package",
    "get_resubmittal_package_record",
    "get_review_cycle",
    "get_review_cycle_dashboard",
    "get_review_cycle_record",
    "get_review_cycle_summary",
    "get_revision_comparison_run",
    "get_revision_comparison_run_record",
    "link_applicant_response_to_resubmittal",
    "link_cad_file_to_resubmittal",
    "list_applicant_responses",
    "list_issue_carry_forwards",
    "list_response_mappings_for_cycle",
    "list_response_resolution_records",
    "list_resubmittal_documents",
    "list_resubmittal_packages",
    "list_review_cycles",
    "list_revision_change_records",
    "list_revision_comparison_runs",
    "prepare_next_cycle",
    "run_revision_comparison",
    "summarize_revision_changes",
    "update_response_resolution_status",
    "update_resubmittal_package_status",
]
