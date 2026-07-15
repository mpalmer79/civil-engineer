"""Cross-domain actor type and evidence role vocabulary."""

from __future__ import annotations

# Evidence roles a finding source may carry. None of these is a conclusion.
ALLOWED_EVIDENCE_ROLES: set[str] = {
    "supports_finding",
    "shows_missing_evidence",
    "shows_conflict",
    "context_only",
    "requires_reviewer_confirmation",
}

# Actor types for real-action attribution. demo_seed marks seeded demo activity;
# reviewer is a real reviewer identity placeholder until real auth exists.
ALLOWED_ACTOR_TYPES: set[str] = {
    "demo_seed",
    "reviewer",
    "system",
    "applicant_placeholder",
    "admin_placeholder",
}

# Actor types for authenticated audit attribution, extending the Sprint 1 set.
ALLOWED_AUTH_ACTOR_TYPES: set[str] = {
    "user",
    "org_admin",
    "reviewer",
    "senior_reviewer",
    "read_only",
    "applicant_placeholder",
    "demo_reviewer",
    "system",
}
