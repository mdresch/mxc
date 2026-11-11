"""Unit tests for the PMBOK process registry."""

from pmbok.models.enums import KnowledgeArea, ProcessGroup
from pmbok.process_registry import (
    PMBOK_PROCESSES,
    PROCESS_DEPENDENCY_MAP,
    get_processes_by_area,
    get_processes_by_group,
)


def test_total_process_count():
    assert len(PMBOK_PROCESSES) == 49


def test_all_knowledge_areas_represented():
    areas = {p.knowledge_area for p in PMBOK_PROCESSES}
    assert areas == set(KnowledgeArea)


def test_all_process_groups_represented():
    groups = {p.process_group for p in PMBOK_PROCESSES}
    assert groups == set(ProcessGroup)


def test_process_ids_are_unique():
    ids = [p.process_id for p in PMBOK_PROCESSES]
    assert len(ids) == len(set(ids))


def test_dependency_map_covers_all_processes():
    registry_ids = {p.process_id for p in PMBOK_PROCESSES}
    map_ids = set(PROCESS_DEPENDENCY_MAP.keys())
    assert registry_ids == map_ids


def test_prerequisites_reference_valid_process_ids():
    registry_ids = {p.process_id for p in PMBOK_PROCESSES}
    for pid, prereqs in PROCESS_DEPENDENCY_MAP.items():
        for prereq in prereqs:
            assert prereq in registry_ids, f"{pid} has unknown prerequisite {prereq}"


def test_prerequisites_populated_on_processes():
    dep_map = PROCESS_DEPENDENCY_MAP
    for p in PMBOK_PROCESSES:
        assert p.prerequisites == dep_map[p.process_id]


def test_expected_outputs_non_empty():
    for p in PMBOK_PROCESSES:
        assert p.expected_outputs, f"Process {p.process_id} has no expected outputs"


def test_get_processes_by_group():
    initiating = get_processes_by_group(ProcessGroup.INITIATING)
    assert len(initiating) == 2
    ids = {p.process_id for p in initiating}
    assert ids == {"4.1", "13.1"}


def test_get_processes_by_area():
    integration = get_processes_by_area(KnowledgeArea.INTEGRATION)
    assert len(integration) == 7
    ids = {p.process_id for p in integration}
    assert ids == {"4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7"}


def test_get_processes_by_group_returns_correct_counts():
    expected = {
        ProcessGroup.INITIATING: 2,
        ProcessGroup.PLANNING: 24,
        ProcessGroup.EXECUTING: 10,
        ProcessGroup.MONITORING_CONTROLLING: 12,
        ProcessGroup.CLOSING: 1,
    }
    for group, count in expected.items():
        result = get_processes_by_group(group)
        assert len(result) == count, f"{group}: expected {count}, got {len(result)}"


def test_key_dependencies():
    """Spot-check a few critical dependency relationships."""
    dep = PROCESS_DEPENDENCY_MAP
    # 4.1 has no prerequisites
    assert dep["4.1"] == []
    # 5.2 requires 5.1
    assert "5.1" in dep["5.2"]
    # 7.2 requires both 7.1 and 6.5
    assert "7.1" in dep["7.2"]
    assert "6.5" in dep["7.2"]
    # 9.2 requires both 9.1 and 5.4
    assert "9.1" in dep["9.2"]
    assert "5.4" in dep["9.2"]
    # 8.1 requires 4.1 and 5.2
    assert "4.1" in dep["8.1"]
    assert "5.2" in dep["8.1"]
    # 4.7 (Closing) has no prerequisites in the map
    assert dep["4.7"] == []
