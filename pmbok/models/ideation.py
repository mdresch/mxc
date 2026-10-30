"""Ideation-related Pydantic models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from pmbok.models.enums import ApprovalStatus


class Conflict(BaseModel):
    field: str
    source_a_id: str
    value_a: str
    source_b_id: str
    value_b: str
    resolved: bool = False
    resolution: str | None = None


class IdeationSummary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    version: int = 1
    title: str
    problem_statement: str
    proposed_solution: str
    key_goals: list[str] = Field(min_length=1)
    assumptions: list[str] = []
    constraints: list[str] = []
    conflicts: list[Conflict] = []
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version_history: list[IdeationSummary] = []

    model_config = {"arbitrary_types_allowed": True}


IdeationSummary.model_rebuild()
