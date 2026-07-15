"""Sentinel values for environment validation.

Environment validation has no runtime exception type; every result is a safe
operational status rather than a raised error. This module holds the sentinel
used to detect an insecure default configuration. The value itself is never
returned by any diagnostic response.
"""

from __future__ import annotations

# The built-in development-only auth secret. A deployment that still uses it is
# flagged for operator review; the value itself is never returned.
_INSECURE_AUTH_SECRET = "dev-only-insecure-change-me"

__all__ = ["_INSECURE_AUTH_SECRET"]
