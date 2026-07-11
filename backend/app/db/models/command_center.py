"""Command center domain: dashboard snapshots, health metrics, attention
items, timeline events, readiness checks, and reviewer notes."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class ProjectCommandCenterSnapshot(Base):
    """A point-in-time aggregated view of the project review-support state."""

    __tablename__ = "command_center_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    current_review_cycle_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    overall_status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    attention_count: Mapped[int] = mapped_column(Integer, default=0)
    ready_for_handoff_count: Mapped[int] = mapped_column(Integer, default=0)
    carry_forward_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_more_information_count: Mapped[int] = mapped_column(Integer, default=0)
    cad_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    resubmittal_count: Mapped[int] = mapped_column(Integer, default=0)
    open_follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    response_mapping_gap_count: Mapped[int] = mapped_column(Integer, default=0)
    revision_change_count: Mapped[int] = mapped_column(Integer, default=0)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ProjectHealthMetric(Base):
    """A single review-support health metric in a command center snapshot."""

    __tablename__ = "project_health_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_route: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ReviewerAttentionItem(Base):
    """A review-support item that needs reviewer attention, with a next step."""

    __tablename__ = "reviewer_attention_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attention_item_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    attention_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    target_route: Mapped[str] = mapped_column(String, nullable=False)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ProjectTimelineEvent(Base):
    """A meaningful review-support event in the project timeline."""

    __tablename__ = "project_timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeline_event_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_title: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    target_route: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=False)


class ReviewReadinessCheck(Base):
    """A review-support readiness check in a command center snapshot."""

    __tablename__ = "review_readiness_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    readiness_check_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    check_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    blocker_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class DashboardReviewerNote(Base):
    """A reviewer note recorded on the project command center dashboard."""

    __tablename__ = "dashboard_reviewer_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_context: Mapped[str | None] = mapped_column(String, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
