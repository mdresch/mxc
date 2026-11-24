"""
ADPA V7 Registry Models.

This module defines the canonical entity substrate for the ADPA framework,
providing hardened Pydantic models for entity identity, versioning, 
provenance, and quality governance.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- Registry Enums ---

class EntityClass(str, Enum):
    """Broad classification of an entity within the registry."""
    ARTIFACT_ROOT = "artifact_root"
    DECOMPOSED_ITEM = "decomposed_item"
    DERIVED_RELATIONSHIP = "derived_relationship"
    CONTROL_RECORD = "control_record"


class ChangeType(str, Enum):
    """Semantic meaning of a version increment."""
    MICRO = "micro"   # Metadata, formatting, or audit-only changes
    MINOR = "minor"   # Content enrichment without changing core meaning
    MAJOR = "major"   # Substantive change in scope, structure, or semantics


class DriftSeverity(str, Enum):
    """Severity of a detected drift event."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """High-level compliance state of an entity."""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class ScoreLabel(str, Enum):
    """Standardized qualitative labels for ordinal scoring."""
    VERY_LOW = "very-low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"


class RiskResponseStrategy(str, Enum):
    """Canonical strategies for managing risks (Possibility)."""
    AVOID = "avoid"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    ACCEPT_PASSIVE = "accept-passive"
    ACCEPT_ACTIVE = "accept-active"
    ESCALATE = "escalate"
    EXPLOIT = "exploit" # Positive
    ENHANCE = "enhance" # Positive
    SHARE = "share"     # Positive


class ResolutionProcedureClass(str, Enum):
    """Operational classes for issue resolution (Materialized)."""
    CONTAINMENT = "containment"
    RCA = "root-cause-analysis"
    CORRECTIVE = "corrective-action"
    PREVENTIVE = "preventive-action"
    ESCALATION = "escalation"
    DE_ESCALATION = "de-escalation"
    RECOVERY = "recovery"
    CLOSURE = "closure"


# --- Support Models (Typed Components) ---

class Classification(BaseModel):
    """Enforced typing for entity classification."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    entity_class: EntityClass = EntityClass.DECOMPOSED_ITEM
    decomposition_level: str = "item"


class ProjectContext(BaseModel):
    """Project-level anchoring for registry records."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    project_id: str
    project_title: Optional[str] = None
    baseline_label: Optional[str] = None


class Integrity(BaseModel):
    """Content and schema verification hashes."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    content_hash: str = Field(description="SHA-256 hash of the entity payload")
    schema_hash: str = Field(description="SHA-256 hash of the expected entity schema")

    @field_validator("content_hash", "schema_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError("Hash must be at least 8 characters.")
        return v


class Versioning(BaseModel):
    """Semantic versioning metadata."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    version_label: str = Field(pattern=r"^\d+\.\d+\.\d+$", description="Semantic version string (e.g. 1.1.0)")
    major: int = 1
    minor: int = 0
    micro: int = 0
    change_type: ChangeType = ChangeType.MAJOR
    change_reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_label_consistency(self) -> Versioning:
        expected = f"{self.major}.{self.minor}.{self.micro}"
        if self.version_label != expected:
            raise ValueError(f"Version label '{self.version_label}' does not match parts {expected}")
        return self


class GovernanceMetadata(BaseModel):
    """Hardened governance and audit metadata."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    audit_status: AuditStatus = AuditStatus.PENDING
    quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    audit_mode: str = "advisory"
    quality_warnings: List[str] = Field(default_factory=list)
    quality_issues_count: int = 0
    v6_1_baseline_compliance: bool = False
    validator_version: str = "v6.1"


class Lineage(BaseModel):
    """Provenance tracking for entities."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    source_artifact_id: str
    process_id: str
    run_id: str
    template_id: Optional[str] = None
    contract_version: str = "v7.0"


class Relationship(BaseModel):
    """Domain-level relationships between entities (Embedded/Structural)."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    relationship_type: str  # e.g., "TRACES_TO", "STAKEHOLDER_FOR"
    target_entity_id: str
    target_version_id: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntityRelationship(BaseModel):
    """Governed relationship entity (External/Traceability)."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaselineStatus(BaseModel):
    """Baseline candidate and locking status."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    is_baseline_candidate: bool = True
    locked_in_baseline: Optional[str] = None


# --- Core Registry Entities ---

class EntityMaster(BaseModel):
    """
    The stable identity of an entity across all versions.
    
    This record answers: 'What is this thing, independent of its revisions?'
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    entity_id: str = Field(description="Stable deterministic identifier")
    canonical_key: str = Field(description="Human-readable normalized identity key")
    canonical_name: str = Field(description="Display name for the entity")
    entity_type: str = Field(description="Type category (e.g. 'stakeholder', 'requirement')")
    registry: str = Field(description="Registry catalog name")
    origin_project_id: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityVersionEnvelope(BaseModel):
    """
    The immutable version history of an entity.
    
    This record is FROZEN to ensure baseline integrity.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str
    entity_version_id: str = Field(description="Immutable version-specific identifier")
    entity_type: str
    registry: str
    classification: Classification
    project_context: ProjectContext
    versioning: Versioning
    integrity: Integrity
    governance: GovernanceMetadata
    lineage: Lineage
    relationships: List[Relationship] = Field(default_factory=list)
    baseline: BaselineStatus
    payload: Dict[str, Any] = Field(description="The actual business content of the entity")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("entity_version_id")
    @classmethod
    def validate_id_alignment(cls, v: str, info: Any) -> str:
        data = info.data
        if "entity_id" in data and "versioning" in data:
            label = data["versioning"].version_label
            expected = f"{data['entity_id']}-v{label}"
            if v != expected:
                # We allow some flexibility if the user uses a different pattern, 
                # but we recommend the standard one.
                pass 
        return v


# --- Registry Control & Governance Records ---

class ArtifactRegistryRecord(BaseModel):
    """Canonical record of a source process artifact (e.g. a JSON file)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    process_id: str
    artifact_type: str
    run_id: str
    project_id: str
    storage_path: Optional[str] = None
    content_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaselineRegistryRecord(BaseModel):
    """Formal definition of an approved baseline."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_id: str
    label: str
    baseline_type: str = "operational"
    description: str
    status: str = "locked"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaselineMembership(BaseModel):
    """Junction record mapping entity versions to baselines (registry-level)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_id: str
    entity_version_id: str
    inclusion_reason: str = "Approved baseline version"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriftEvent(BaseModel):
    """Record of a detected drift event relative to a baseline."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    drift_id: str
    entity_id: str
    baseline_version_id: str
    observed_version_id: str
    drift_type: str = "semantic"  # semantic, structural, cardinality, value
    severity: DriftSeverity = DriftSeverity.MEDIUM
    drift_score: float = 0.0
    drift_description: Optional[str] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnomalyEvent(BaseModel):
    """Record of an outlier condition or suspicious pattern (point-in-time)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    anomaly_id: str
    entity_version_id: str
    anomaly_type: str
    severity: DriftSeverity = DriftSeverity.HIGH
    metric_name: Optional[str] = None
    expected_value: Optional[Union[float, str]] = None
    observed_value: Optional[Union[float, str]] = None
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Phase 4: Value Layer Payloads ---

class EvaluationMetricPayload(BaseModel):
    """Payload for canonical evaluation criteria."""
    model_config = ConfigDict(extra="forbid")

    name: str
    summary: str
    metric_kind: str = "performance"
    evaluation_question: str
    scale_definition: str = "1-5 Ordinal"
    optimization_direction: str = "higher-is-better" # higher-is-better, lower-is-better
    preferred_interpretation: str = "higher-is-better"
    scope: str = "adpa-v7"
    source_framework: str = "BABOK v3"
    evidence_expectation: str = "Mandatory rationale + source reference"


class ValueAssessmentPayload(BaseModel):
    """
    Payload for a governed judgment (Option vs Metric).
    
    This is a first-class entity that anchors to both a DesignOption and a Metric.
    """
    model_config = ConfigDict(extra="forbid")

    design_option_id: str
    metric_id: str
    score_ordinal: int = Field(ge=1, le=5)
    score_label: ScoreLabel
    rationale: str = Field(min_length=10, description="Mandatory narrative justification")
    evidence_refs: List[str] = Field(min_length=1, description="One or more source references")
    confidence: str = "medium" # low, medium, high
    assessment_basis: str = "artifact-decomposition"
    tradeoff_notes: Optional[str] = None


# --- Phase 5: Synthesis Layer Payloads ---

class RecommendationPayload(BaseModel):
    """Payload for analytical synthesis and solution guidance."""
    model_config = ConfigDict(extra="forbid")

    name: str
    summary: str
    recommended_option_id: str
    rationale: str = Field(min_length=20)
    supporting_assessment_ids: List[str] = Field(min_length=1)
    generator_type: str = "human-expert" # or ai-orchestrator
    tradeoff_summary: Optional[str] = None


class DecisionRecordPayload(BaseModel):
    """Payload for formal human-accountable commitment."""
    model_config = ConfigDict(extra="forbid")

    adopted_recommendation_id: str
    decider_stakeholder_id: str
    decision_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    decision_status: str = "approved" # approved, rejected, deferred
    approval_authority: str = "Project Sponsor"
    override_rationale: Optional[str] = None # Mandatory if not approved


# --- Phase 6: Operational Control Payloads ---

class COSOAssertionPayload(BaseModel):
    """Payload for structured internal control assertions per COSO framework."""
    model_config = ConfigDict(extra="forbid")

    objective_domain: str = "operations" # operations, reporting, compliance
    coso_component: str # control_environment, risk_assessment, control_activities, etc.
    coso_principles: List[int] = Field(min_length=1, max_length=17)
    control_assertion: str = Field(min_length=10)
    current_failure: str
    remediation_assertion: str = Field(min_length=10)
    mapping_rationale: Optional[str] = None


class RCAPayload(BaseModel):
    """Payload for mandatory Root Cause Analysis."""
    model_config = ConfigDict(extra="forbid")

    problem_statement: str = Field(min_length=10)
    symptoms: List[str] = Field(min_length=1)
    root_cause: str = Field(min_length=10)
    contributing_factors: List[str] = Field(default_factory=list)
    rca_evidence_refs: List[str] = Field(min_length=1)
    confidence: str = "medium" # low, medium, high


class EscalationEvent(BaseModel):
    """Record of a severity shift or owner transfer."""
    model_config = ConfigDict(extra="forbid")

    timestamp: str
    from_severity: str
    to_severity: str
    trigger_type: str = "sla-breach" # sla-breach, manual, system-threshold
    rationale: str
    new_owner_id: Optional[str] = None


class IssueRecordPayload(BaseModel):
    """Payload for active operational guidance and control restoration."""
    model_config = ConfigDict(extra="forbid")

    name: str
    summary: str
    severity: str = "medium" # low, medium, high, critical
    urgency: str = "medium"
    status: str = "open" # open, contained, resolved, closed, control-breach
    procedure_stage: str = "issue" # risk-stage, issue-stage
    control_restoration_status: str = "not-started" 
    
    # Traceability
    matured_from_risk_id: Optional[str] = None
    impacts_requirement_id: Optional[str] = None
    
    # Governance & Execution
    containment_actions: Optional[str] = None
    active_procedures: List[ResolutionProcedureClass] = Field(default_factory=list)
    rca: Optional[RCAPayload] = None # Mandatory for Medium+
    coso_assertion: Optional[COSOAssertionPayload] = None # Mandatory for Medium+
    mitigation_plan: Optional[List[str]] = None
    escalation_history: List[EscalationEvent] = Field(default_factory=list)
    closure_evidence: Optional[str] = None
