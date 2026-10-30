"""PMBOK process and project run Pydantic models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

from pmbok.models.enums import (
    ApprovalStatus,
    KnowledgeArea,
    ProcessGroup,
    ProcessStatus,
)

if TYPE_CHECKING:
    from pmbok.models.audit import AuditResult


class PMBOKProcess(BaseModel):
    process_id: str
    name: str
    knowledge_area: KnowledgeArea
    process_group: ProcessGroup
    prerequisites: list[str] = []
    expected_outputs: list[str] = []


class ProjectArtifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    process_id: str
    artifact_type: str
    version: int = 1
    content: dict[str, Any]
    produced_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    previous_version_id: str | None = None
    audit_result: Optional["AuditResult"] = None
    """Optional audit result attached to this artifact."""


class ProcessState(BaseModel):
    process_id: str
    run_id: str
    status: ProcessStatus = ProcessStatus.NOT_STARTED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempt_count: int = 0
    error_log: list[str] = []
    output_artifact_ids: list[str] = []


class ProcessMap(BaseModel):
    run_id: str
    processes: list[ProcessState]
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_case_id: str
    current_process_group: ProcessGroup = ProcessGroup.INITIATING
    gate_status: dict[ProcessGroup, ApprovalStatus] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


# Rebuild ProjectArtifact model after all types are imported
def _rebuild_models():
    """Rebuild models with proper type resolution."""
    try:
        from pmbok.models.audit import AuditResult  # noqa: F401
        ProjectArtifact.model_rebuild()
    except ImportError:
        # If audit models aren't imported yet, that's okay
        pass


_rebuild_models()
