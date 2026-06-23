"""Database engine, session factory, and declarative base.

SQLite is used for local Phase 2 storage. The connection setup is written so a
later move to PostgreSQL or Supabase only requires changing DATABASE_URL.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# check_same_thread is a SQLite specific flag needed because FastAPI may use the
# connection across threads. It is ignored by other database backends.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Models are imported for side effect registration."""

    from app.db import models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
