"""Phase 13 multi-round resubmittal, revision comparison, and response cycle API.

These endpoints manage review cycles, resubmittal packages, applicant responses
and mappings, DXF metadata revision comparison, issue carry-forward, response
resolution, and next-cycle preparation. Revision comparison compares extracted
DXF metadata only. No endpoint verifies CAD, validates design, certifies
compliance, or makes a final engineering decision, and there is no action called
approve.

Read side effects: GET /review-cycles/{id}, /review-cycle-dashboard,
/revision-comparisons/{id}, /revision-comparisons/{id}/changes,
/response-mapping-summary, /carry-forward-summary, /resolution-summary, and
/next-cycle-preparation each write an audit event recording reviewer access. This
is intentional so the decision history shows reviewer access.

Access control: project-scoped routes guard on the path project_id. Routes keyed
by a raw entity id (review cycle, resubmittal, comparison run, applicant response,
resolution record) resolve the owning project first so a raw id cannot bypass
tenant access. The public Brookside Meadows demo project stays readable.

This module was split into a package. The endpoint handlers live in cohesive
submodules that all register on a single shared router, imported here in the
original route order. The public surface is unchanged: app.api.routes still does
`from app.api.v1 import review_cycle` then `review_cycle.router`.
"""

from __future__ import annotations

from app.api.v1.review_cycle._common import router

# Import each submodule so its route decorators register on the shared router.
# The import order preserves the original registration order.
from app.api.v1.review_cycle import cycles  # noqa: E402,F401
from app.api.v1.review_cycle import resubmittals  # noqa: E402,F401
from app.api.v1.review_cycle import responses  # noqa: E402,F401
from app.api.v1.review_cycle import comparison  # noqa: E402,F401
from app.api.v1.review_cycle import carry_forward  # noqa: E402,F401
from app.api.v1.review_cycle import resolution  # noqa: E402,F401
from app.api.v1.review_cycle import next_cycle  # noqa: E402,F401

__all__ = ["router"]
