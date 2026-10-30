"""Reporting Pydantic models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from pmbok.models.enums import KnowledgeArea


class StatusCounts(BaseModel):
    not_started: int = 0
    in_progress: int = 0
    complete: int = 0
    blocked: int = 0


class ProgressReport(BaseModel):
    run_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    by_knowledge_area: dict[KnowledgeArea, StatusCounts]
    total: StatusCounts
