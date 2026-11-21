"""Contract tests for Story 2.2 — No wake-caused 502/504.

Governing documents:
- Epic: docs/user-stories/epic-002-connection-buffering-ingress-gateway.md
- ADR: docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md (§4.4)
- BRD: docs/project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md (BRU-002-04)
- FDD: docs/project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md (§Error Handling)
- WBS: WBS 3.2 (Saturation handling & zero wake errors)
- Benefits Statement: BEN-03 (Zero wake-caused HTTP 502 or 504)
- Hypotheses: HYP-mxc-010

Acceptance Criteria:
- AC1: Given normal conditions, when the guest wakes, then response is not HTTP 502 or 504
       because of wake (AC-01.3, BEN-03).
- AC2: Given wake exceeds wake_timeout_ms, when timer fires, then HTTP 503 with Retry-After
       is returned.
"""

from __future__ import annotations

import pytest

from ingress_gateway import (
    IngressGateway,
    IngressRequest,
    IngressResponse,
    VMTargetState,
)


def test_ac1_normal_wake_never_returns_502_or_504() -> None:
    """Story 2.2 (ADR-002 / BRU-002-04) AC-1:

    Given normal conditions, when the guest wakes, then response is not HTTP 502 or 504
    because of wake (AC-01.3, BEN-03).
    """
    gateway = IngressGateway(wake_timeout_ms=3000.0)
    gateway.register_target(
        pool_id="prod-adpa",
        initial_state=VMTargetState.PAUSED,
        simulated_unpause_latency_ms=250.0,
        simulated_app_latency_ms=50.0,
    )

    req = IngressRequest(
        method="POST",
        path="/api/v1/adpa/settle-batch",
        headers={"Content-Type": "application/json"},
        body=b'{"batch_id": "BATCH-001"}',
    )

    response: IngressResponse = gateway.handle_request(req)

    # Core invariant: wake latency never surfaces as 502 or 504
    assert response.status_code not in (502, 504), (
        f"Wake caused forbidden gateway error code {response.status_code} (violates BEN-03 / BRU-002-04)"
    )
    assert response.status_code == 200
    assert response.was_cold_wake is True
    assert response.connection_buffer_held is True


def test_ac2_wake_timeout_returns_http_503_with_retry_after() -> None:
    """Story 2.2 (ADR-002 / BRU-002-04) AC-2:

    Given wake exceeds wake_timeout_ms, when timer fires, then HTTP 503 with Retry-After
    is returned.
    """
    gateway = IngressGateway(wake_timeout_ms=2000.0)
    # Target configured with wake delay exceeding 2000ms wake_timeout_ms
    gateway.register_target(
        pool_id="prod-adpa",
        initial_state=VMTargetState.PAUSED,
        simulated_unpause_latency_ms=2500.0,  # exceeds wake_timeout_ms
        simulated_app_latency_ms=50.0,
    )

    req = IngressRequest(
        method="POST",
        path="/api/v1/adpa/settle-batch",
        headers={"Content-Type": "application/json"},
        body=b'{"batch_id": "BATCH-002"}',
    )

    response: IngressResponse = gateway.handle_request(req)

    # Must return 503 Service Unavailable, NEVER 502/504
    assert response.status_code == 503
    assert response.status_code not in (502, 504)
    assert "Retry-After" in response.headers
    assert response.headers["Retry-After"] == "2"
    assert b"Service Unavailable" in response.body
    assert b"wake_timeout_ms" in response.body
