"""Unit tests for RegistryRepository."""

import pytest
from datetime import datetime, timezone
from pmbok.registry.repository import RegistryRepository
from pmbok.models.registry import (
    EntityMaster,
    EntityVersionEnvelope,
    Versioning,
    Integrity,
    ProjectContext,
    Classification,
    EntityClass,
    Lineage,
    GovernanceMetadata,
    BaselineStatus,
    BaselineRegistryRecord,
    BaselineMembership,
    DriftEvent,
    DriftSeverity,
    AnomalyEvent,
    ChangeType
)

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_registry.db")

@pytest.fixture
def repo(db_path):
    return RegistryRepository(db_path)

@pytest.mark.asyncio
async def test_ensure_master_idempotency(repo):
    master = EntityMaster(
        entity_id="ENT-001",
        canonical_key="stakeholder_list",
        canonical_name="Stakeholder Register",
        entity_type="stakeholder",
        registry="stakeholder_registry",
        origin_project_id="PRJ-001"
    )
    
    # First save
    await repo.ensure_master(master)
    
    # Reload
    loaded = await repo.get_master("ENT-001")
    assert loaded is not None
    assert loaded.canonical_key == "stakeholder_list"
    assert loaded.canonical_name == "Stakeholder Register"
    
    # Second save (should be ignored)
    await repo.ensure_master(master)
    
    loaded2 = await repo.get_master("ENT-001")
    assert loaded2.entity_id == "ENT-001"

@pytest.mark.asyncio
async def test_save_and_get_version(repo):
    # Setup master first
    master = EntityMaster(
        entity_id="ENT-001",
        canonical_key="req_1",
        canonical_name="Requirement 1",
        entity_type="requirement",
        registry="req_registry",
        origin_project_id="PRJ-001"
    )
    await repo.ensure_master(master)
    
    envelope = EntityVersionEnvelope(
        entity_id="ENT-001",
        entity_version_id="ENT-001-v1.0.0",
        entity_type="requirement",
        registry="req_registry",
        classification=Classification(entity_class=EntityClass.DECOMPOSED_ITEM),
        project_context=ProjectContext(project_id="PRJ-001"),
        versioning=Versioning(version_label="1.0.0", major=1, minor=0, micro=0, change_type=ChangeType.MAJOR),
        integrity=Integrity(content_hash="sha256:abc1234567", schema_hash="sha256:def6789012"),
        governance=GovernanceMetadata(quality_score=95.0, audit_mode="advisory"),
        lineage=Lineage(source_artifact_id="ART-001", process_id="1.1", run_id="RUN-001"),
        baseline=BaselineStatus(),
        payload={"text": "Hello Registry"}
    )
    
    await repo.save_version(envelope)
    
    # Reload
    loaded = await repo.get_version("ENT-001-v1.0.0")
    assert loaded is not None
    assert loaded.payload == {"text": "Hello Registry"}
    assert loaded.governance.quality_score == 95.0
    assert loaded.versioning.version_label == "1.0.0"

@pytest.mark.asyncio
async def test_baseline_operations(repo):
    baseline = BaselineRegistryRecord(
        baseline_id="BSL-001",
        label="v1.0.0",
        baseline_type="operational",
        description="First project baseline",
        status="locked"
    )
    
    await repo.create_baseline(baseline)
    
    # Versions for members
    master = EntityMaster(
        entity_id="E1", canonical_key="K1", canonical_name="N1", 
        entity_type="T1", registry="R1", origin_project_id="P1"
    )
    await repo.ensure_master(master)
    
    v1 = EntityVersionEnvelope(
        entity_id="E1", entity_version_id="E1-v1.0.0", entity_type="T1", registry="R1",
        classification=Classification(entity_class=EntityClass.DECOMPOSED_ITEM),
        project_context=ProjectContext(project_id="P1"),
        versioning=Versioning(version_label="1.0.0", major=1, minor=0, micro=0),
        integrity=Integrity(content_hash="sha256:h12345678", schema_hash="sha256:h22345678"),
        governance=GovernanceMetadata(),
        lineage=Lineage(source_artifact_id="A1", process_id="1", run_id="R1"),
        baseline=BaselineStatus(),
        payload={}
    )
    await repo.save_version(v1)
    
    membership = BaselineMembership(
        baseline_id="BSL-001",
        entity_version_id="E1-v1.0.0",
        inclusion_reason="Initial baseline"
    )
    await repo.add_to_baseline(membership)
    
    members = await repo.get_baseline_members("BSL-001")
    assert "E1-v1.0.0" in members

@pytest.mark.asyncio
async def test_event_logging(repo):
    drift = DriftEvent(
        drift_id="DRF-001",
        entity_id="ENT-001",
        baseline_version_id="v1",
        observed_version_id="v2",
        severity=DriftSeverity.HIGH,
        drift_description="Major changes detected"
    )
    await repo.log_drift(drift)
    
    anomaly = AnomalyEvent(
        anomaly_id="ANM-001",
        entity_version_id="ENT-001-v2",
        anomaly_type="OUTLIER",
        severity=DriftSeverity.HIGH,
        description="Suspicious pattern detected",
        metric_name="outlier_score",
        observed_value=0.88
    )
    await repo.log_anomaly(anomaly)
