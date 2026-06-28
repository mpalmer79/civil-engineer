"""Pydantic schemas for public pilot / design-partner requests.

A pilot request is a public lead captured from the marketing site. It is not
tenant-owned project data and carries no review-support state or final-decision
language. No uploaded file content is accepted here; has_sample_package only
records that the submitter said they have a sample package to test.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# A deliberately simple email shape check. This is prototype-grade validation,
# not full RFC 5322 parsing, and it does not verify deliverability.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Allowed interest levels. Kept as a small closed set so the stored value stays
# predictable for any future follow-up workflow.
ALLOWED_INTEREST_LEVELS: set[str] = {
    "exploring",
    "evaluating",
    "ready_to_pilot",
}

# Operator pipeline statuses for a design-partner conversation. These describe the
# outreach state of a lead only; they carry no review-support or engineering
# meaning. "new" is the default assigned at creation.
PILOT_STATUSES: tuple[str, ...] = (
    "new",
    "contacted",
    "qualified",
    "active_pilot",
    "closed",
    "rejected",
)


class PilotRequestCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    work_email: str = Field(min_length=3, max_length=320)
    firm_name: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    project_type: str = Field(min_length=1, max_length=200)
    primary_pain: str = Field(min_length=1, max_length=4000)
    interest_level: str = Field(min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=4000)
    has_sample_package: bool = False

    @field_validator("work_email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        cleaned = value.strip()
        if not _EMAIL_PATTERN.match(cleaned):
            raise ValueError("A valid work email is required.")
        return cleaned

    @field_validator("interest_level")
    @classmethod
    def _validate_interest(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in ALLOWED_INTEREST_LEVELS:
            raise ValueError(
                "interest_level must be one of: "
                + ", ".join(sorted(ALLOWED_INTEREST_LEVELS))
            )
        return cleaned


class PilotRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pilot_request_id: str
    full_name: str
    work_email: str
    firm_name: str
    role_title: str
    project_type: str
    primary_pain: str
    interest_level: str
    notes: str | None = None
    has_sample_package: bool = False
    source: str | None = None
    status: str = "new"
    internal_notes: str | None = None
    last_contacted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PilotRequestStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=40)
    # Optional flag to stamp last_contacted_at to now when an operator records an
    # outreach. No prospect data is sent anywhere.
    mark_contacted: bool = False

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in PILOT_STATUSES:
            raise ValueError(
                "status must be one of: " + ", ".join(PILOT_STATUSES)
            )
        return cleaned


class PilotRequestNotesUpdate(BaseModel):
    internal_notes: str | None = Field(default=None, max_length=8000)


class PilotRequestAck(BaseModel):
    """Honest acknowledgement returned after a successful submission.

    The request is recorded only. No email is sent, because no email provider is
    configured, and no data leaves this system.
    """

    pilot_request_id: str
    received: bool = True
    message: str = (
        "Thanks. Your pilot request was received. This prototype is currently "
        "accepting design-partner conversations. We will follow up before "
        "requesting any real project files."
    )
