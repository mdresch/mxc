"""Contract tests for Story 1.1 — Generation 2 isolation boundary.

Governing documents:
- Epic: docs/user-stories/epic-001-type-1-hyperv-generation-2.md
- ADR: docs/07-architecture/ADR-001-type-1-hyperv-generation-2.md
- BRD: docs/project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md (BRU-001-01, BRU-001-02)
- FDD: docs/project-docs/Functional-Design/FDD-001-type-1-hyperv-generation-2.md
- WBS: WBS 2.1 (Generation 2 isolation boundary)

Recommended contract interpretations derived by scripts/spec_gate.py:
- [I1] Empty Collection Base Case:
      "Passing zero records or an empty sequence must return an empty result without raising an error."
"""

from __future__ import annotations

import pytest

from hyperv_isolation import (
    IsolationType,
    PoolMemberDescriptor,
    ProposalDecision,
    WorkloadProposal,
    evaluate_workload_proposal,
    validate_pool_member_isolation,
    validate_pool_members,
)


def test_ac1_generation_2_and_distinct_guest_kernel() -> None:
    """Story 1.1 (ADR-001) AC-1:

    Given a new pool member, when provisioned, then Hyper-V reports Generation 2
    and a guest kernel distinct from the host.
    """
    # Member with Generation 2 and distinct guest kernel
    member = PoolMemberDescriptor(
        sandbox_id="hv:a7df7452",
        vm_name="mxc-hv-a7df7452",
        generation=2,
        host_kernel_version="10.0.26100.1742",
        guest_kernel_version="10.0.26100.2161",
        isolation_type=IsolationType.HYPERV_GEN2,
    )
    result = validate_pool_member_isolation(member)
    assert result.is_valid is True
    assert result.generation == 2
    assert result.guest_kernel != result.host_kernel
    assert "Generation 2" in result.summary

    # Member with Generation 1 must be rejected
    gen1_member = PoolMemberDescriptor(
        sandbox_id="hv:legacy01",
        vm_name="mxc-hv-legacy01",
        generation=1,
        host_kernel_version="10.0.26100.1742",
        guest_kernel_version="10.0.26100.2161",
        isolation_type=IsolationType.HYPERV_GEN1,
    )
    gen1_result = validate_pool_member_isolation(gen1_member)
    assert gen1_result.is_valid is False
    assert "Generation 2 required" in gen1_result.rejection_reason

    # Member sharing the host kernel must be rejected
    shared_kernel_vm = PoolMemberDescriptor(
        sandbox_id="hv:shared01",
        vm_name="mxc-hv-shared01",
        generation=2,
        host_kernel_version="10.0.26100.1742",
        guest_kernel_version="10.0.26100.1742",  # identical to host
        isolation_type=IsolationType.HYPERV_GEN2,
    )
    shared_result = validate_pool_member_isolation(shared_kernel_vm)
    assert shared_result.is_valid is False
    assert "distinct guest kernel" in shared_result.rejection_reason.lower()


def test_ac2_shared_kernel_container_proposal_rejected_with_bru_001_02() -> None:
    """Story 1.1 (ADR-001) AC-2:

    Given a shared-kernel container proposal for the same records, when evaluated
    against this epic, then it is rejected with reference to BRU-001-02.
    """
    container_proposal = WorkloadProposal(
        workload_id="adpa-confidential-payroll",
        is_confidential=True,
        isolation_type=IsolationType.CONTAINER_SHARED_KERNEL,
        runtime_name="process-container",
    )
    decision = evaluate_workload_proposal(container_proposal)
    assert decision.decision == ProposalDecision.REJECTED
    assert "BRU-001-02" in decision.governing_rule
    assert "ADR-001" in decision.justification
    assert decision.isolation_allowed is False

    # Conversely, a Type-1 Hyper-V Gen 2 proposal for the same records is accepted
    hyperv_proposal = WorkloadProposal(
        workload_id="adpa-confidential-payroll",
        is_confidential=True,
        isolation_type=IsolationType.HYPERV_GEN2,
        runtime_name="wxc-exec --features hyperv",
    )
    accepted_decision = evaluate_workload_proposal(hyperv_proposal)
    assert accepted_decision.decision == ProposalDecision.ACCEPTED
    assert accepted_decision.isolation_allowed is True
    assert "BRU-001-01" in accepted_decision.governing_rule


def test_i1_empty_collection_base_case() -> None:
    """Story 1.1 (ADR-001) Interpretation I1:

    Passing zero records or an empty sequence must return an empty result without raising an error.
    """
    empty_results = validate_pool_members([])
    assert empty_results == []
    assert isinstance(empty_results, list)
