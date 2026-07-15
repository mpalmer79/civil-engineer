"""Workflow bounded context: workflow board items, reviewer actions, and follow-up requests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow

class WorkflowItem(Base):
    """An operational workflow board item tracking a review-support item.

    Phase 9 promotes review packet items into a reviewer workflow board so a
    human reviewer can move each item from triage through follow-up to handoff.
    A workflow item tracks where a review-support item sits in the operational
    review workflow. It does not approve plans, certify compliance, stamp
    drawings, verify CAD, validate a design, or make final engineering
    decisions. Every item stays under human control.
    """

    __tablename__ = "workflow_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_item_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    packet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    packet_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_types: Mapped[list] = mapped_column(JSON, default=list)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowAction(Base):
    """A persisted reviewer action on a workflow item.

    Each action records a status transition or note a reviewer made while
    working the board. There is no action called approve, and no action
    approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "workflow_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowFollowUpRequest(Base):
    """A follow-up request tracked against a workflow item.

    A reviewer may request more information or a follow-up from an applicant or
    another reviewer. The request records what was asked and its status. It
    never records a final engineering decision; closing a request without a
    decision is an explicit allowed state.
    """

    __tablename__ = "workflow_follow_up_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    follow_up_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    requested_from: Mapped[str] = mapped_column(String, nullable=False)
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_information: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
