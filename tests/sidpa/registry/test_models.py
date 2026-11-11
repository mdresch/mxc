import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from pmbok.models.registry import (
    EntityVersionEnvelope, 
    EntityMaster, 
    Versioning, 
    Integrity, 
    GovernanceMetadata, 
    Lineage, 
    BaselineStatus,
    Classification,
    ProjectContext,
    ChangeType,
    AuditStatus,
    EntityClass
)

def test_versioning_label_consistency():
    # Valid consistency
    v = Versioning(version_label="1.2.3", major=1, minor=2, micro=3, change_type=ChangeType.MINOR)
    assert v.version_label == "1.2.3"

    # Invalid consistency
    with pytest.raises(ValidationError) as excinfo:
        Versioning(version_label="1.2.4", major=1, minor=2, micro=3)
    assert "Version label '1.2.4' does not match parts 1.2.3" in str(excinfo.value)

def test_integrity_hash_validation():
    # Valid hashes
    i = Integrity(content_hash="sha256:12345678", schema_hash="sha256:87654321")
    assert i.content_hash == "sha256:12345678"

    # Invalid hashes (too short)
    with pytest.raises(ValidationError):
        Integrity(content_hash="short", schema_hash="also_short")

def test_governance_score_bounds():
    # Valid scores
    g = GovernanceMetadata(quality_score=100.0, audit_status=AuditStatus.PASS)
    assert g.quality_score == 100.0

    # Invalid scores (out of bounds)
    with pytest.raises(ValidationError):
        GovernanceMetadata(quality_score=100.1)
    with pytest.raises(ValidationError):
        GovernanceMetadata(quality_score=-0.1)

def test_envelope_immutability():
    # Setup envelope
    env = EntityVersionEnvelope(
        entity_id="ENT-001",
        entity_version_id="ENT-001-v1.0.0",
        entity_type="requirement",
        registry="requirement_registry",
        classification=Classification(entity_class=EntityClass.DECOMPOSED_ITEM),
        project_context=ProjectContext(project_id="PRJ-001"),
        versioning=Versioning(version_label="1.0.0", major=1, minor=0, micro=0),
        integrity=Integrity(content_hash="sha256:hash1", schema_hash="sha256:hash2"),
        governance=GovernanceMetadata(),
        lineage=Lineage(source_artifact_id="ART-001", process_id="1.1", run_id="RUN-001"),
        baseline=BaselineStatus(),
        payload={"text": "Requirement 1"}
    )

    # Attempt to modify a field (should fail because frozen=True)
    with pytest.raises(ValidationError):
        env.entity_id = "ENT-002"

def test_entity_master_mutability():
    # Setup master
    master = EntityMaster(
        entity_id="ENT-001",
        canonical_key="req-1",
        canonical_name="Requirement 1",
        entity_type="requirement",
        registry="requirement_registry",
        origin_project_id="PRJ-001"
    )

    # Attempt to modify status (should succeed because it's not frozen)
    master.status = "archived"
    assert master.status == "archived"

    # Attempt to add an extra field (should fail because extra="forbid")
    with pytest.raises(ValidationError):
        master.something_else = "wrong"

def test_timezone_aware_timestamps():
    master = EntityMaster(
        entity_id="ENT-001",
        canonical_key="req-1",
        canonical_name="Requirement 1",
        entity_type="requirement",
        registry="requirement_registry",
        origin_project_id="PRJ-001"
    )
    # Check that it's timezone-aware
    assert master.created_at.tzinfo is not None
    assert master.created_at.tzinfo == timezone.utc

def test_relationship_targeting():
    from pmbok.models.registry import Relationship
    
    # Target by entity ID
    r1 = Relationship(relationship_type="TRACES_TO", target_entity_id="ENT-002")
    assert r1.target_entity_id == "ENT-002"
    assert r1.target_version_id is None

    # Target by specific version
    r2 = Relationship(relationship_type="TRACES_TO", target_entity_id="ENT-002", target_version_id="ENT-002-v1.0.0")
    assert r2.target_version_id == "ENT-002-v1.0.0"
