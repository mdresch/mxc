"""Contract tests for Story 2.1 — Cold wake TTFB.

Governing documents:
- Epic: docs/user-stories/epic-002-connection-buffering-ingress-gateway.md
- ADR: docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md (§4.2, §4.3)
- BRD: docs/project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md (BRU-002-01, BRU-002-02)
- FDD: docs/project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md (§Design)
- WBS: WBS 3.1 (Cold wake TTFB & connection hold)
- Benefits Statement: BEN-02 (Wake without a cold boot: 300 ms unpause and 800 ms first byte)
- Hypotheses: HYP-mxc-003

Acceptance Criteria:
- AC1: Given target VM Paused, when POST arrives, then gateway holds, wakes,
       and first byte ≤ 800 ms (AC-01.1, BEN-02).
- AC2: Given VM Running, when subsequent requests arrive, then proxy overhead
       ≤ 5 ms plus app time (AC-01.2).
"""

from __future__ import annotations

import pytest

from ingress_gateway import (
    ConnectionBufferState,
    IngressGateway,
    IngressRequest,
    IngressResponse,
    VMTargetState,
)


def test_ac1_cold_wake_from_paused_vm_ttfb_under_800ms() -> None:
    """Story 2.1 (ADR-002 / BRU-002-01, BRU-002-02) AC-1:

    Given target VM Paused, when POST arrives, then gateway holds, wakes,
    and first byte ≤ 800 ms (AC-01.1).
    """
    gateway = IngressGateway(wake_timeout_ms=3000.0)

    # Configure target VM initially in PAUSED state (simulated 220ms unpause + 45ms health probe)
    target = gateway.register_target(
        pool_id="prod-adpa",
        initial_state=VMTargetState.PAUSED,
        simulated_unpause_latency_ms=220.0,
        simulated_app_latency_ms=80.0,
    )

    req = IngressRequest(
        method="POST",
        path="/api/v1/adpa/process-record",
        headers={"Content-Type": "application/json"},
        body=b'{"record_id": "REC-9941"}',
    )

    response: IngressResponse = gateway.handle_request(req)

    # Verification: request was buffered, VM awakened, and TTFB <= 800ms
    assert response.status_code == 200
    assert response.was_cold_wake is True
    assert response.connection_buffer_held is True
    assert response.ttfb_ms <= 800.0, f"Cold wake TTFB exceeded 800ms: {response.ttfb_ms}ms"
    assert response.target_vm_state == VMTargetState.RUNNING


def test_ac2_warm_path_proxy_overhead_under_5ms() -> None:
    """Story 2.1 (ADR-002 / BRU-002-02) AC-2:

    Given VM Running, when subsequent requests arrive, then proxy overhead
    ≤ 5 ms plus app time (AC-01.2).
    """
    gateway = IngressGateway(wake_timeout_ms=3000.0)

    # Configure target VM in active RUNNING state (warm path)
    target = gateway.register_target(
        pool_id="prod-adpa",
        initial_state=VMTargetState.RUNNING,
        simulated_unpause_latency_ms=0.0,
        simulated_app_latency_ms=30.0,
    )

    req = IngressRequest(
        method="POST",
        path="/api/v1/adpa/process-record",
        headers={"Content-Type": "application/json"},
        body=b'{"record_id": "REC-9942"}',
    )

    response: IngressResponse = gateway.handle_request(req)

    assert response.status_code == 200
    assert response.was_cold_wake is False
    assert response.connection_buffer_held is False
    # Proxy overhead must be <= 5ms
    assert response.proxy_overhead_ms <= 5.0, (
        f"Warm proxy overhead exceeded 5ms: {response.proxy_overhead_ms}ms"
    )
    # Total duration = app latency + proxy overhead
    expected_ceiling = 30.0 + 5.0
    assert response.ttfb_ms <= expected_ceiling
