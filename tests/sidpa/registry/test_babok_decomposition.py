import pytest
import json
from pathlib import Path
from pmbok.orchestrator.registry_manager import RegistryManager
from pmbok.registry.repository import RegistryRepository
from pmbok.models.registry import EntityClass

@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_registry.db"
    return RegistryRepository(str(db_path))

@pytest.fixture
def manager(repo):
    return RegistryManager(repo)

@pytest.mark.asyncio
async def test_decompose_design_options_from_business_case(manager):
    # Mock Business Case Artifact from Meta-Run V2
    artifact = {
        "artifact_type": "Business Case",
        "artifact_id": "bc-123",
        "project_id": "ADPA-V7-BABOK",
        "run_id": "run-456",
        "process_id": "v2-bc",
        "content": {
            "proposed_solution": "Direct integration of BABOK Knowledge Areas.",
            "recommendation": "Adopt the registry-first approach.",
            "design_options": [
                {
                    "name": "Option A: Registry-First",
                    "summary": "Focus on substrate models.",
                    "rationale": "High governance value."
                },
                {
                    "name": "Option B: Agent-First",
                    "summary": "Focus on generator prompts.",
                    "rationale": "High immediate speed."
                }
            ]
        }
    }

    report = await manager.register_artifact(artifact)
    
    assert report.total_discovered == 2
    assert report.registered_new == 2
    
    # Verify Master Identities
    # project_id + business_need_id (bn-discovery) + slug
    # slug A: option-a-registry-first
    # slug B: option-b-agent-first
    
    # Check Repo
    all_masters = await manager.repo.list_masters()
    keys = [m.canonical_key for m in all_masters]
    assert "design-option:adpa-v7-babok:bn-discovery:option-a-registry-first" in keys
    assert "design-option:adpa-v7-babok:bn-discovery:option-b-agent-first" in keys
    
    # Verify Type
    master = await manager.repo.get_master_by_key("design-option:adpa-v7-babok:bn-discovery:option-a-registry-first")
    assert master.entity_type == "design_option"
    assert master.registry == "babok.design_option"
