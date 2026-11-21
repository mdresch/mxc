"""Type-1 Hyper-V Generation 2 isolation boundary and container rejection logic.

Governed by ADR-001, BRD-001 (BRU-001-01, BRU-001-02), FDD-001, and Story 1.1 (WBS 2.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class IsolationType(str, Enum):
    """Runtime isolation environment types."""
    HYPERV_GEN2 = "hyperv_gen2"
    HYPERV_GEN1 = "hyperv_gen1"
    CONTAINER_SHARED_KERNEL = "container_shared_kernel"
    HOST_DIRECT = "host_direct"


class ProposalDecision(str, Enum):
    """Adjudication verdict for workload runtime proposals."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PoolMemberDescriptor:
    """Descriptor for a provisioned Hyper-V sandbox pool member."""
    sandbox_id: str
    vm_name: str
    generation: int
    host_kernel_version: str
    guest_kernel_version: str
    isolation_type: IsolationType = IsolationType.HYPERV_GEN2


@dataclass(frozen=True)
class MemberValidationResult:
    """Result of evaluating a pool member's isolation boundary."""
    sandbox_id: str
    is_valid: bool
    generation: int
    host_kernel: str
    guest_kernel: str
    summary: str
    rejection_reason: str = ""


@dataclass(frozen=True)
class WorkloadProposal:
    """Proposal to execute a confidential or standard workload in a designated runtime."""
    workload_id: str
    is_confidential: bool
    isolation_type: IsolationType
    runtime_name: str


@dataclass(frozen=True)
class ProposalEvaluation:
    """Decision output for a workload runtime proposal."""
    workload_id: str
    decision: ProposalDecision
    isolation_allowed: bool
    governing_rule: str
    justification: str


def validate_pool_member_isolation(member: PoolMemberDescriptor) -> MemberValidationResult:
    """Validate that a pool member satisfies Story 1.1 / ADR-001 AC-1 constraints:

    - Generation must be exactly 2.
    - Guest kernel version must be distinct from the host kernel version.
    """
    if member.generation != 2:
        return MemberValidationResult(
            sandbox_id=member.sandbox_id,
            is_valid=False,
            generation=member.generation,
            host_kernel=member.host_kernel_version,
            guest_kernel=member.guest_kernel_version,
            summary=f"VM {member.vm_name} generation is {member.generation}",
            rejection_reason=f"Generation 2 required; found Generation {member.generation} (violates BRU-001-01 and ADR-001)",
        )

    if member.guest_kernel_version == member.host_kernel_version:
        return MemberValidationResult(
            sandbox_id=member.sandbox_id,
            is_valid=False,
            generation=member.generation,
            host_kernel=member.host_kernel_version,
            guest_kernel=member.guest_kernel_version,
            summary=f"VM {member.vm_name} shares the host kernel ({member.host_kernel_version})",
            rejection_reason="Workload requires distinct guest kernel; guest and host kernels are identical",
        )

    return MemberValidationResult(
        sandbox_id=member.sandbox_id,
        is_valid=True,
        generation=member.generation,
        host_kernel=member.host_kernel_version,
        guest_kernel=member.guest_kernel_version,
        summary=f"VM {member.vm_name} provisioned as Generation 2 with distinct guest kernel {member.guest_kernel_version}",
        rejection_reason="",
    )


def validate_pool_members(members: Sequence[PoolMemberDescriptor]) -> list[MemberValidationResult]:
    """Validate a sequence of pool members.

    Handles empty collection base case (Interpretation I1) without error.
    """
    if not members:
        return []
    return [validate_pool_member_isolation(m) for m in members]


def evaluate_workload_proposal(proposal: WorkloadProposal) -> ProposalEvaluation:
    """Evaluate a workload execution proposal against Story 1.1 / ADR-001 AC-2.

    If the workload processes confidential records and requests a shared-kernel container,
    reject with reference to BRU-001-02 and ADR-001.
    """
    if proposal.is_confidential and proposal.isolation_type == IsolationType.CONTAINER_SHARED_KERNEL:
        return ProposalEvaluation(
            workload_id=proposal.workload_id,
            decision=ProposalDecision.REJECTED,
            isolation_allowed=False,
            governing_rule="BRU-001-02",
            justification=(
                "Shared-kernel container proposal rejected per BRU-001-02 and ADR-001 §4.2: "
                "confidential workloads (ADPA/SIDPA) require dedicated hardware boundary (Type-1 Hyper-V Gen 2)."
            ),
        )

    if proposal.isolation_type == IsolationType.HYPERV_GEN2:
        return ProposalEvaluation(
            workload_id=proposal.workload_id,
            decision=ProposalDecision.ACCEPTED,
            isolation_allowed=True,
            governing_rule="BRU-001-01",
            justification="Type-1 Hyper-V Generation 2 satisfies isolation boundary requirements per ADR-001 §4.1.",
        )

    return ProposalEvaluation(
        workload_id=proposal.workload_id,
        decision=ProposalDecision.REJECTED,
        isolation_allowed=False,
        governing_rule="BRU-001-01",
        justification=f"Unsupported isolation type {proposal.isolation_type.value}; Type-1 Hyper-V Gen 2 required.",
    )
