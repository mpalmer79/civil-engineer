"""Authorization actor context and error types.

Re-exported from the auth foundation so callers of access_control_service keep a
single import surface for the actor context and auth error type.
"""

from __future__ import annotations

from app.services.auth_service import ActorContext, AuthError

__all__ = ["ActorContext", "AuthError"]
