"""Pydantic schemas for documents."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    project_id: str
    file_name: str
    document_type: str
    status: str
    purpose: str
    expected_key_information: str
    intentionally_missing_or_conflicting_information: str | None = None
