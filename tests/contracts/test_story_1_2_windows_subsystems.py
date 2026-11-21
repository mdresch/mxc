"""Contract tests for Story 1.2 — Windows subsystems on the guest.

Governing documents:
- Epic: docs/user-stories/epic-001-type-1-hyperv-generation-2.md
- ADR: docs/07-architecture/ADR-001-type-1-hyperv-generation-2.md (§4.3, Context 4)
- BRD: docs/project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md (BRU-001-03)
- FDD: docs/project-docs/Functional-Design/FDD-001-type-1-hyperv-generation-2.md (Verification Hooks)
- WBS: WBS 2.2 (Windows subsystems on guest)
- Benefits Statement: BEN-05 (Windows automation subsystems remain in scope)
- Hypotheses: HYP-mxc-009

Acceptance Criteria:
- AC1: Given the Generation 2 guest from Story 1.1, when each named subsystem (WMI, COM+,
       Windows Services, Group Policy) is invoked, then the call succeeds in the guest.
- AC2: Given the same calls attempted in a container namespace baseline, then they fail
       or are unsupported, and the difference is recorded for BEN-05.
"""

from __future__ import annotations

import pytest

from hyperv_subsystems import (
    DifferentialAuditRecord,
    ExecutionEnvironment,
    SubsystemInvocationResult,
    WindowsSubsystem,
    execute_subsystem_probe,
    record_differential_audit,
    run_full_subsystem_suite,
)


def test_ac1_named_subsystems_succeed_in_generation_2_guest() -> None:
    """Story 1.2 (ADR-001 / BRU-001-03) AC-1:

    Given the Generation 2 guest from Story 1.1, when each named subsystem
    (WMI, COM+, Windows Services, Group Policy) is invoked, then the call succeeds in the guest.
    """
    env = ExecutionEnvironment.GENERATION_2_GUEST
    suite_result = run_full_subsystem_suite(env)

    assert suite_result.environment == ExecutionEnvironment.GENERATION_2_GUEST
    assert suite_result.all_succeeded is True
    assert len(suite_result.results) == 4

    subsystems_tested = {r.subsystem for r in suite_result.results}
    assert subsystems_tested == {
        WindowsSubsystem.WMI,
        WindowsSubsystem.COM_PLUS,
        WindowsSubsystem.WINDOWS_SERVICES,
        WindowsSubsystem.GROUP_POLICY,
    }

    for result in suite_result.results:
        assert result.succeeded is True
        assert result.exit_code == 0
        assert result.error_message == ""
        assert "succeeded in Generation 2 guest" in result.detail


def test_ac2_subsystems_fail_or_unsupported_in_container_and_recorded_for_ben_05() -> None:
    """Story 1.2 (ADR-001 / BEN-05) AC-2:

    Given the same calls attempted in a container namespace baseline, then they fail
    or are unsupported, and the difference is recorded for BEN-05.
    """
    container_env = ExecutionEnvironment.CONTAINER_NAMESPACE
    container_result = run_full_subsystem_suite(container_env)

    assert container_result.environment == ExecutionEnvironment.CONTAINER_NAMESPACE
    assert container_result.all_succeeded is False

    # In container namespace, legacy automation subsystems fail or report unsupported
    for res in container_result.results:
        assert res.succeeded is False
        assert res.exit_code != 0 or res.is_supported is False
        assert len(res.error_message) > 0

    # Record and verify differential audit against BEN-05
    gen2_result = run_full_subsystem_suite(ExecutionEnvironment.GENERATION_2_GUEST)
    audit: DifferentialAuditRecord = record_differential_audit(
        guest_results=gen2_result,
        container_results=container_result,
        benefit_id="BEN-05",
    )

    assert audit.benefit_id == "BEN-05"
    assert audit.traceable_adr == "ADR-001"
    assert audit.traceable_bru == "BRU-001-03"
    assert audit.guest_success_count == 4
    assert audit.container_success_count == 0
    assert audit.parity_gap_confirmed is True
    assert len(audit.differences) == 4

    # Verify each subsystem difference is recorded
    diff_subsystems = {d.subsystem for d in audit.differences}
    assert diff_subsystems == {
        WindowsSubsystem.WMI,
        WindowsSubsystem.COM_PLUS,
        WindowsSubsystem.WINDOWS_SERVICES,
        WindowsSubsystem.GROUP_POLICY,
    }
