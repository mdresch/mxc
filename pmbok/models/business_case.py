"""Business case Pydantic models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from pmbok.models.enums import ApprovalStatus


class CostItem(BaseModel):
    label: str
    amount: float | None = None
    currency: str = "USD"
    is_placeholder: bool = False


class BusinessCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ideation_summary_id: str
    version: int = 1
    executive_summary: str
    problem_statement: str
    proposed_solution: str
    expected_benefits: list[str]
    estimated_costs: list[CostItem]
    key_risks: list[str]
    recommendation: str
    placeholders: list[str] = []
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version_history: list[BusinessCase] = []

    model_config = {"arbitrary_types_allowed": True}


BusinessCase.model_rebuild()
