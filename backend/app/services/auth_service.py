"""Local authentication foundation for Civil Engineer AI (Sprint 5).

This module provides a simple, secure, dependency-light local authentication
layer: PBKDF2-HMAC-SHA256 password hashing and HMAC-SHA256 signed access tokens
(the same HS256 construction a JWT uses), both from the Python standard library.
It is a local auth foundation, not enterprise SSO. It protects review records and
improves audit attribution; it grants no engineering authority and never makes a
final engineering decision.

Security properties:
- Passwords are never stored in plaintext; only a salted PBKDF2 hash is kept.
- Password hashes are never returned by the API.
- Tokens are signed with AUTH_SECRET_KEY and carry a short expiry. Tokens are
  never logged and never stored in audit metadata.
- Password verification and token signature checks use constant-time comparison.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 120_000
_TOKEN_ALG = "HS256"


class AuthError(Exception):
    """Raised when an authentication operation fails."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class ActorContext:
    """Resolved actor identity for attribution and access decisions.

    Built from a signed-in user, or from the demo reviewer fallback when demo
    mode is on. Carries no secrets.
    """

    display_name: str
    actor_type: str
    user_id: str | None = None
    user_email: str | None = None
    organization_id: str | None = None
    access_level: str | None = None
    is_demo: bool = False


def audit_kwargs(actor: "ActorContext | None") -> dict:
    """Return record_audit_event user-attribution kwargs for an actor context.

    Carries only identity fields; never tokens, passwords, or hashes.
    """

    if actor is None:
        return {}
    return {
        "user_id": actor.user_id,
        "user_email": actor.user_email,
        "organization_id": actor.organization_id,
        "access_level": actor.access_level,
    }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-HMAC-SHA256 hash string for a password."""

    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return (
        f"pbkdf2_{_PBKDF2_ALGORITHM}${_PBKDF2_ITERATIONS}$"
        f"{salt.hex()}${derived.hex()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash in constant time."""

    try:
        scheme, iterations_str, salt_hex, hash_hex = password_hash.split("$")
        if not scheme.startswith("pbkdf2_"):
            return False
        algorithm = scheme.split("_", 1)[1]
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    derived = hashlib.pbkdf2_hmac(
        algorithm, password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(derived, expected)


# ---------------------------------------------------------------------------
# Tokens (HS256 signed, JWT-compatible construction)
# ---------------------------------------------------------------------------


def _sign(message: bytes) -> str:
    secret = get_settings().AUTH_SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).digest()
    return _b64encode(signature)


def create_access_token(
    user: models.UserAccount, *, expires_minutes: int | None = None
) -> str:
    """Create a signed access token for a user. The token carries no secret."""

    settings = get_settings()
    minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.AUTH_TOKEN_EXPIRE_MINUTES
    )
    issued = _now()
    expires = issued + timedelta(minutes=minutes)
    header = {"alg": _TOKEN_ALG, "typ": "JWT"}
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "iat": int(issued.timestamp()),
        "exp": int(expires.timestamp()),
    }
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _sign(signing_input)
    return f"{header_b64}.{payload_b64}.{signature}"


def decode_access_token(token: str) -> dict:
    """Validate a token's signature and expiry and return its payload claims."""

    try:
        header_b64, payload_b64, signature = token.split(".")
    except (ValueError, AttributeError) as exc:
        raise AuthError("Invalid token.", status_code=401) from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthError("Invalid token signature.", status_code=401)
    try:
        payload = json.loads(_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("Invalid token payload.", status_code=401) from exc
    exp = payload.get("exp")
    if exp is None or int(exp) < int(_now().timestamp()):
        raise AuthError("Token has expired. Sign in again.", status_code=401)
    return payload


# ---------------------------------------------------------------------------
# User accounts
# ---------------------------------------------------------------------------


def get_user_by_email(db: Session, email: str) -> models.UserAccount | None:
    normalized = (email or "").strip().lower()
    return db.scalars(
        select(models.UserAccount).where(models.UserAccount.email == normalized)
    ).first()


def get_user(db: Session, user_id: str) -> models.UserAccount | None:
    return db.get(models.UserAccount, user_id)


def create_user(
    db: Session,
    *,
    email: str,
    display_name: str,
    password: str,
    is_demo_user: bool = False,
) -> models.UserAccount:
    """Create a user account with a hashed password."""

    settings = get_settings()
    normalized = (email or "").strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise AuthError("A valid email address is required.", status_code=422)
    if len(password or "") < settings.AUTH_MIN_PASSWORD_LENGTH:
        raise AuthError(
            "Password must be at least "
            f"{settings.AUTH_MIN_PASSWORD_LENGTH} characters.",
            status_code=422,
        )
    if not (display_name or "").strip():
        raise AuthError("A display name is required.", status_code=422)
    if get_user_by_email(db, normalized) is not None:
        raise AuthError(
            "An account with this email already exists.", status_code=409
        )
    now = _now()
    user = models.UserAccount(
        user_id=f"user_{_short()}",
        email=normalized,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        is_active=True,
        is_demo_user=is_demo_user,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()
    return user


def authenticate_user(
    db: Session, *, email: str, password: str
) -> models.UserAccount:
    """Return the user if the email and password match and the account is active."""

    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Incorrect email or password.", status_code=401)
    if not user.is_active:
        raise AuthError("This account is not active.", status_code=403)
    user.last_login_at = _now()
    db.flush()
    return user


def get_current_user_from_token(
    db: Session, token: str | None
) -> models.UserAccount | None:
    """Resolve the user from a bearer token, or None when no valid token."""

    if not token:
        return None
    payload = decode_access_token(token)
    user = get_user(db, payload.get("sub", ""))
    if user is None or not user.is_active:
        raise AuthError("User not found or inactive.", status_code=401)
    return user


def user_public_dict(user: models.UserAccount) -> dict:
    """Return a safe public dict for a user. Never includes the password hash."""

    return {
        "user_id": user.user_id,
        "email": user.email,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "is_demo_user": user.is_demo_user,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }
