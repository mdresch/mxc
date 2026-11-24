"""Input-related Pydantic models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from pmbok.models.enums import InputSourceType


class RawInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: InputSourceType
    filename: str
    data: bytes
    size_bytes: int
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}


class ParsedInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_input_id: str
    extracted_text: str
    diagram_description: str | None = None
    source_type: InputSourceType
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class FailedItem(BaseModel):
    raw_input_id: str
    filename: str
    reason: str


class BatchResult(BaseModel):
    session_id: str
    successful: list[ParsedInput]
    failed: list[FailedItem]
