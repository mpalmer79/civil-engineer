"""Safe Alembic migration status for the readiness API.

Reports whether the connected database is migration-managed and whether it is at
the latest migration, without exposing any secret. The current and head revision
identifiers are short Alembic hashes, not connection details, so they are safe to
return. Every lookup is guarded so a readiness check never fails because of a
migration-status probe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# backend/ directory, where alembic.ini and app/migrations live.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"


def _head_revision() -> str | None:
    """Return the latest migration revision from the script directory, or None."""

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        if not _ALEMBIC_INI.exists():
            return None
        config = Config(str(_ALEMBIC_INI))
        config.set_main_option("script_location", str(_BACKEND_DIR / "app" / "migrations"))
        script = ScriptDirectory.from_config(config)
        return script.get_current_head()
    except Exception:  # noqa: BLE001 - status probe must never raise
        return None


def _current_revision(db: Session) -> str | None:
    """Return the revision recorded in alembic_version, or None if unmanaged."""

    try:
        inspector = inspect(db.get_bind())
        if "alembic_version" not in inspector.get_table_names():
            return None
        row = db.execute(text("SELECT version_num FROM alembic_version")).first()
        return row[0] if row else None
    except Exception:  # noqa: BLE001 - status probe must never raise
        return None


def get_migration_status(db: Session) -> dict[str, Any]:
    """Return a safe migration-status summary for readiness.

    managed is True when the database carries an alembic_version table (it is
    under migration control). When the schema was created by the create_all
    convenience path instead, managed is False and the database is reported as
    "unmanaged" rather than out of date. No secret is included.
    """

    head = _head_revision()
    current = _current_revision(db)

    if current is None:
        # No alembic_version table: schema created by create_all (dev/test/pilot)
        # or not yet migrated. This is not an error, just unmanaged.
        return {
            "managed": False,
            "status": "unmanaged",
            "current_revision": None,
            "head_revision": head,
            "message": (
                "Schema is not under Alembic control (create_all convenience "
                "path). Run 'alembic upgrade head' for migration-managed "
                "deployments."
            ),
        }

    if head is not None and current == head:
        status = "up_to_date"
        message = "Database schema is at the latest migration."
    elif head is None:
        status = "managed"
        message = "Database is migration-managed; latest revision is unknown."
    else:
        status = "behind"
        message = (
            "Database is migration-managed but behind the latest migration. Run "
            "'alembic upgrade head'."
        )

    return {
        "managed": True,
        "status": status,
        "current_revision": current,
        "head_revision": head,
        "message": message,
    }
