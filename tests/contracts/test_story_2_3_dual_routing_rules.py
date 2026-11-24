"""Contract tests for Story 2.3 — Dual routing rules.

Governing documents:
- Epic: docs/user-stories/epic-002-connection-buffering-ingress-gateway.md
- ADR: docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md (§4.5)
- BRD: docs/project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md (BRU-002-03)
- FDD: docs/project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md (§Design, §Route schema)
- WBS: WBS 3.3 (Dual routing rules: path & port)
- Benefits Statement: BEN-04 (The request lands on the owning image)
- Hypotheses: HYP-mxc-004

Recommended contract interpretations derived by scripts/spec_gate.py:
- [I1] Empty Collection Base Case:
      "Passing zero records or an empty sequence must return an empty result without raising an error."

Acceptance Criteria:
- AC1: Given path `/api/v1/adpa`, when leased, then pool is `prod-adpa` and
       the check records path routing (HYP-mxc-004).
- AC2: Given listen port `:8091`, when accepted, then image is the catalogued
       ADPA PoC image and the check records port routing.
"""

from __future__ import annotations

import pytest

from ingress_gateway import (
    IngressGateway,
    IngressRequest,
    IngressResponse,
    RoutingRuleType,
    VMTargetState,
    batch_resolve_routes,
)


def test_ac1_path_routing_selects_pool_and_records_path_rule() -> None:
    """Story 2.3 (ADR-002 / BRU-002-03 / HYP-mxc-004) AC-1:

    Given path `/api/v1/adpa`, when leased, then pool is `prod-adpa` and
    the check records path routing.
    """
    gateway = IngressGateway()
    gateway.register_target(pool_id="prod-adpa", initial_state=VMTargetState.RUNNING)
    gateway.register_target(pool_id="prod-sidpa", initial_state=VMTargetState.RUNNING)

    # Test /api/v1/adpa path routing
    adpa_req = IngressRequest(
        method="POST",
        path="/api/v1/adpa/claims/verify",
        headers={"Content-Type": "application/json"},
        body=b'{}',
    )
    adpa_resp: IngressResponse = gateway.handle_request(adpa_req)
    assert adpa_resp.status_code == 200
    assert adpa_resp.routed_pool_id == "prod-adpa"
    assert adpa_resp.routing_rule_fired == RoutingRuleType.PATH

    # Test /api/v1/sidpa path routing
    sidpa_req = IngressRequest(
        method="POST",
        path="/api/v1/sidpa/lifecycle/advance",
        headers={"Content-Type": "application/json"},
        body=b'{}',
    )
    sidpa_resp: IngressResponse = gateway.handle_request(sidpa_req)
    assert sidpa_resp.status_code == 200
    assert sidpa_resp.routed_pool_id == "prod-sidpa"
    assert sidpa_resp.routing_rule_fired == RoutingRuleType.PATH


def test_ac2_port_routing_selects_catalogued_image_and_records_port_rule() -> None:
    """Story 2.3 (ADR-002 / BRU-002-03 / BEN-04) AC-2:

    Given listen port `:8091`, when accepted, then image is the catalogued
    ADPA PoC image and the check records port routing.
    """
    gateway = IngressGateway()
    gateway.register_target(pool_id="prod-adpa", initial_state=VMTargetState.RUNNING)

    # Request arriving on listen port 8091
    port_req = IngressRequest(
        method="POST",
        path="/workload/invoke",
        headers={"Content-Type": "application/json"},
        body=b'{}',
        incoming_port=8091,
    )
    port_resp: IngressResponse = gateway.handle_request(port_req)

    assert port_resp.status_code == 200
    assert port_resp.routed_image_name == "mxc-adpa-poc-golden:latest"
    assert port_resp.routed_pool_id == "prod-adpa"
    assert port_resp.routing_rule_fired == RoutingRuleType.PORT

    # Verify ports 8090 (dev image) and 8092 (SIDPA dev image)
    dev_req = IngressRequest(method="GET", path="/", incoming_port=8090)
    dev_resp = gateway.handle_request(dev_req)
    assert dev_resp.routed_image_name == "mxc-servercore-dev-golden:latest"
    assert dev_resp.routing_rule_fired == RoutingRuleType.PORT

    sidpa_dev_req = IngressRequest(method="GET", path="/", incoming_port=8092)
    sidpa_dev_resp = gateway.handle_request(sidpa_dev_req)
    assert sidpa_dev_resp.routed_image_name == "mxc-sidpa-dev-golden:latest"
    assert sidpa_dev_resp.routing_rule_fired == RoutingRuleType.PORT


def test_i1_empty_collection_base_case() -> None:
    """Story 2.3 Interpretation I1:

    Passing zero records or an empty sequence must return an empty result without raising an error.
    """
    empty_routes = batch_resolve_routes(gateway=IngressGateway(), requests=[])
    assert empty_routes == []
    assert isinstance(empty_routes, list)
