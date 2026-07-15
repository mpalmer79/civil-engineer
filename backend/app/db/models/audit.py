"""Audit bounded context: the project audit event trail."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Non-sensitive structured context (provider, prompt version, chunk ids,
    # validation and safety status). Never stores secrets or API keys.
    event_metadata: Mapped[dict] = mapped_column("event_metadata", JSON, default=dict)
    # Production foundation fields (Sprint 1). Actor attribution and request
    # context for real reviewer actions. Raw IP and user agent are never stored;
    # only optional hashes are kept, and only when a caller chooses to provide
    # them. These are nullable so seeded and existing audit events keep working.
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_ip_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    # Production foundation fields (Sprint 5). When an action is taken by a
    # signed-in user, the audit event records the user and organization identity
    # for real attribution. Tokens, passwords, and password hashes are never
    # stored here. Nullable so seeded and demo-attributed events keep working.
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_email: Mapped[str | None] = mapped_column(String, nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    access_level: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="audit_events")


@event.listens_for(AuditEvent, "before_insert")
def _default_request_id(_mapper, _connection, target: "AuditEvent") -> None:
    """Fill the correlation id from the current request when a caller omits it.

    The request middleware binds a correlation id for the request context. This
    listener copies it onto every audit row that does not already carry one, so
    the audit trail can be joined to the access logs for a single request. It
    only sets request_id and never overrides an explicit value or any other
    attribution field.
    """

    if target.request_id:
        return
    from app.core.request_context import get_request_id

    request_id = get_request_id()
    if request_id:
        target.request_id = request_id
