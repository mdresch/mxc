"""Approval-related Pydantic models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from pmbok.models.enums import ApprovalStatus


class ApprovalDecision(BaseModel):
    status: ApprovalStatus
    revision_instructions: str | None = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)
