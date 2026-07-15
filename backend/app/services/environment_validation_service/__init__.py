"""Environment validation and deployment diagnostics (Sprint 10).

Civil Engineer AI validates critical environment configuration so an operator can
confirm a deployment is wired correctly before relying on it. Every result is a
safe operational status. This service never returns secret values: it reports
whether a setting is configured, never what it is. Database URLs, the auth secret,
object storage credentials, tokens, and raw file system paths are never included
in any response.

These checks describe configuration and connectivity readiness only. They do not
approve a project, certify compliance, verify CAD, validate design, declare
safety, resolve an issue, or close an issue.

This module was split into a package (errors, database, storage, config, report,
_common). The public surface is unchanged: both
`from app.services import environment_validation_service` and
`from app.services.environment_validation_service import <name>` keep working.
"""

from __future__ import annotations

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

from app.services.environment_validation_service.errors import _INSECURE_AUTH_SECRET
from app.services.environment_validation_service._common import (
    _bool_hint,
    _item,
)
from app.services.environment_validation_service.database import _database_items
from app.services.environment_validation_service.storage import (
    _object_storage_items,
    _storage_items,
)
from app.services.environment_validation_service.config import (
    _application_items,
    _authentication_items,
    _cors_items,
    _frontend_integration_items,
    _public_demo_items,
)
from app.services.environment_validation_service.report import (
    get_frontend_config_diagnostics,
    get_readiness,
    get_security_boundary_diagnostics,
    get_storage_diagnostics,
    validate_environment,
    _overall_status,
    _readiness_overall,
)

__all__ = [
    "validate_environment",
    "get_readiness",
    "get_storage_diagnostics",
    "get_frontend_config_diagnostics",
    "get_security_boundary_diagnostics",
]
