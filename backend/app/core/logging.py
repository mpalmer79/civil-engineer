"""Safe structured logging helpers (Production Foundations Sprint 10).

Civil Engineer AI logs operational status to help an operator understand
deployment health. Logs must never contain secrets or private content. This
module provides a small structured logger and a redaction helper that removes
secret-like fields before anything is written.

It is intentionally lightweight: standard library logging only, no external APM,
no Sentry, no OpenTelemetry. The redaction list is conservative so a new
secret-like key is masked by default rather than leaked.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER_NAME = "civil_engineer"

# Substrings that mark a field as sensitive. Matching is case insensitive against
# the lowercased key name, so AUTH_SECRET_KEY, OBJECT_STORAGE_SECRET_ACCESS_KEY,
# password_hash, access_token, and similar are all masked. The list is broad on
# purpose: it is safer to mask an innocuous field than to leak a secret.
_SENSITIVE_KEY_PARTS: tuple[str, ...] = (
    "secret",
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "credential",
    "private",
    "signed_url",
    "authorization",
    "session",
)

# Keys whose value is a path or location we never log verbatim. The value is
# replaced with a safe marker so logs cannot leak a server file system layout.
_PATH_LIKE_KEY_PARTS: tuple[str, ...] = (
    "path",
    "dir",
    "directory",
    "database_url",
    "db_url",
    "dsn",
    "storage_key",
    "endpoint_url",
)

_REDACTED = "[redacted]"
_OMITTED = "[set]"


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _SENSITIVE_KEY_PARTS)


def _is_path_like(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _PATH_LIKE_KEY_PARTS)


def redact(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of data with secret-like and path-like values masked.

    A secret-like field is replaced with "[redacted]". A path-like field is
    reported only as "[set]" or "[empty]" so an operator can see whether it is
    configured without learning the value. Nested dicts are redacted recursively.
    The input is not mutated.
    """

    safe: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            safe[key] = redact(value)
            continue
        if _is_sensitive(key):
            safe[key] = _REDACTED if value not in (None, "", False) else "[empty]"
            continue
        if _is_path_like(key):
            safe[key] = _OMITTED if value not in (None, "") else "[empty]"
            continue
        safe[key] = value
    return safe


def get_logger() -> logging.Logger:
    """Return the shared application logger, configured once."""

    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(event: str, /, *, level: int = logging.INFO, **fields: Any) -> None:
    """Log a structured operational event with secret-like fields redacted.

    The event name is a short stable label (for example "startup_configuration").
    Fields are redacted before formatting, so callers may pass a configuration
    summary without first removing secrets. Values are rendered as key=value.
    """

    safe = redact(fields)
    rendered = " ".join(f"{key}={value}" for key, value in safe.items())
    get_logger().log(level, "%s %s", event, rendered)
