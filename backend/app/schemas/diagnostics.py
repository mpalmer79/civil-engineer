"""Pydantic schemas for deployment diagnostics (Production Foundations Sprint 10).

These describe safe operational status only. No schema carries a secret value, a
database URL, an auth secret, object storage credentials, a token, a signed URL,
or a raw file system path. Statuses are operational readiness indicators, never a
final engineering or compliance outcome.
"""

from __future__ import annotations

from pydantic import BaseModel


class ReadinessCheck(BaseModel):
    category: str
    status: str
    message: str


class ReadinessResponse(BaseModel):
    status: str
    service: str
    version: str
    demo_mode: bool
    checks: list[ReadinessCheck]


class EnvironmentValidationItem(BaseModel):
    category: str
    key: str
    status: str
    severity: str
    message: str
    required: bool
    configured: bool
    public_hint: str | None = None
    remediation_hint: str | None = None


class EnvironmentValidationResponse(BaseModel):
    overall_status: str
    item_count: int
    status_counts: dict[str, int]
    items: list[EnvironmentValidationItem]


class StorageDiagnosticsResponse(BaseModel):
    provider: str
    configured: bool
    status: str
    message: str
    items: list[EnvironmentValidationItem]


class FrontendConfigDiagnosticsResponse(BaseModel):
    api_prefix: str
    expects_backend_origin_only: bool
    frontend_env_var: str
    guidance: list[str]


class SecurityBoundaryDiagnosticsResponse(BaseModel):
    summary: str
    prohibited_outcome_terms: list[str]
    diagnostics_are_operational_only: bool
