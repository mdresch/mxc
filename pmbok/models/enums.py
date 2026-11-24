"""Enumeration types for the PMBOK system."""

from __future__ import annotations

from enum import Enum


class ProcessStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    BLOCKED = "blocked"


class AuditMode(str, Enum):
    BLOCKING = "blocking"
    ADVISORY = "advisory"


class KnowledgeArea(str, Enum):
    INTEGRATION = "Integration"
    SCOPE = "Scope"
    SCHEDULE = "Schedule"
    COST = "Cost"
    QUALITY = "Quality"
    RESOURCE = "Resource"
    COMMUNICATIONS = "Communications"
    RISK = "Risk"
    PROCUREMENT = "Procurement"
    STAKEHOLDER = "Stakeholder"


class ProcessGroup(str, Enum):
    INITIATING = "Initiating"
    PLANNING = "Planning"
    EXECUTING = "Executing"
    MONITORING_CONTROLLING = "Monitoring & Controlling"
    CLOSING = "Closing"


class InputSourceType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
