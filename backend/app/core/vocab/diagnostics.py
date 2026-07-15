"""Deployment, environment validation, and observability diagnostics vocabulary."""

from __future__ import annotations

# Production Foundations Sprint 10 deployment hardening, environment validation,
# and observability vocabulary. Diagnostics describe operational readiness only.
# A status, severity, or category never approves a project, certifies compliance,
# verifies CAD, validates design, declares safety, resolves an issue, or closes an
# issue. There is intentionally no approved, certified, verified, passed, failed,
# compliant, noncompliant, safe, or unsafe value anywhere in this vocabulary.

# Diagnostic categories an environment validation item may belong to. These group
# configuration checks for operator review only.
ALLOWED_DIAGNOSTIC_CATEGORIES: set[str] = {
    "application",
    "database",
    "authentication",
    "storage",
    "object_storage",
    "public_demo",
    "cors",
    "deployment",
    "frontend_integration",
}

# Diagnostic status values for environment, readiness, and storage checks. Each
# describes a configuration or connectivity state, never an engineering outcome.
# needs_operator_review asks a human operator to look at a setting; it is not a
# failure determination.
ALLOWED_DIAGNOSTIC_STATUSES: set[str] = {
    "ready",
    "configured",
    "missing_required",
    "missing_optional",
    "warning",
    "disabled",
    "unavailable",
    "needs_operator_review",
}

# Diagnostic severity levels. These rank operator attention only.
ALLOWED_DIAGNOSTIC_SEVERITIES: set[str] = {
    "info",
    "notice",
    "warning",
    "critical",
}
