"""Contract tests for Story 5.2 — Egress whitelist (WBS 6.2).

Acceptance Criteria:
- AC1: Given active guest, when connection targets public internet, then it is dropped (AC-02.3).
- AC2: Given SQL, PostgreSQL, private blob, DNS, and Kerberos to approved endpoints,
       then connections are allowed.
- Inbound: Only port 8080 from reverse proxy allowed; all other inbound dropped.
- Hyper-V ACL generation: Verify Add-VMNetworkAdapterAcl configuration matches specification.
"""

import pytest
from scripts.lib.session_sterility import (
    SessionDiskManager,
    NetworkCheckResult,
    WHITELISTED_EGRESS_PORTS,
    INGRESS_ALLOWED_PORT,
    generate_hyperv_port_acls,
    is_approved_internal_endpoint,
)


class TestStory52EgressWhitelist:
    """Validate egress filtering, inbound ACLs, and Hyper-V vSwitch ACL generation."""

    @pytest.fixture
    def manager(self):
        return SessionDiskManager()

    # -------------------------------------------------------------------------
    # AC1: Public internet connections dropped
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("destination,port", [
        ("8.8.8.8", 53),
        ("1.1.1.1", 53),
        ("93.184.216.34", 80),
        ("140.82.121.4", 443),
        ("api.github.com", 443),
        ("google.com", 443),
        ("public_internet", 1433),
        ("external_untrusted", 5432),
        ("203.0.113.10", 22),
        ("198.51.100.25", 8080),
    ])
    def test_public_internet_egress_dropped(self, manager, destination, port):
        """AC1 (AC-02.3): All egress targeting public internet or unapproved endpoints is dropped."""
        result: NetworkCheckResult = manager.evaluate_outbound_traffic(
            destination=destination,
            port=port,
            protocol="TCP" if port != 53 else "UDP",
        )
        assert result.action == "DROP", f"Expected DROP for {destination}:{port}, got {result.action}"
        assert not result.is_allowed
        assert "DROP" in result.reason or "prohibited" in result.reason or "Default-deny" in result.reason

    # -------------------------------------------------------------------------
    # AC2: Approved internal endpoints on whitelisted ports allowed
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("destination,port,protocol,expected_desc", [
        ("10.0.0.10", 53, "UDP", "DNS"),
        ("dc01.corp.internal", 53, "UDP", "DNS"),
        ("10.0.0.10", 88, "TCP", "Kerberos"),
        ("kdc.corp.internal", 88, "TCP", "Kerberos"),
        ("10.1.0.50", 1433, "TCP", "SQL Server"),
        ("sql-cluster.corp.internal", 1433, "TCP", "SQL Server"),
        ("10.1.0.60", 5432, "TCP", "PostgreSQL"),
        ("pg-analytics.corp.internal", 5432, "TCP", "PostgreSQL"),
        ("10.2.0.100", 443, "TCP", "Private Blob Storage"),
        ("corpstorage.privatelink.blob.core.windows.net", 443, "TCP", "Private Blob Storage"),
    ])
    def test_approved_internal_endpoints_allowed(self, manager, destination, port, protocol, expected_desc):
        """AC2: SQL, PostgreSQL, private blob, DNS, Kerberos to approved endpoints are allowed."""
        result: NetworkCheckResult = manager.evaluate_outbound_traffic(
            destination=destination,
            port=port,
            protocol=protocol,
        )
        assert result.action == "ALLOW", f"Expected ALLOW for {destination}:{port}, got {result.action}"
        assert result.is_allowed
        assert expected_desc in result.reason

    def test_internal_endpoint_on_non_whitelisted_port_dropped(self, manager):
        """Even if destination is internal, non-whitelisted ports (e.g. SSH :22) are dropped."""
        result = manager.evaluate_outbound_traffic(
            destination="10.1.0.50",
            port=22,
            protocol="TCP",
        )
        assert result.action == "DROP"
        assert not result.is_allowed

    # -------------------------------------------------------------------------
    # Inbound ACL: Ingress proxy only
    # -------------------------------------------------------------------------
    def test_inbound_traffic_allowed_only_on_ingress_proxy_port(self, manager):
        """Inbound traffic permitted solely on TCP 8080 from reverse proxy."""
        # 8080 allowed
        inbound_8080 = manager.evaluate_inbound_traffic(source="10.0.0.5", port=INGRESS_ALLOWED_PORT)
        assert inbound_8080.action == "ALLOW"
        assert inbound_8080.is_allowed

        # Other inbound ports dropped
        for blocked_port in [80, 443, 22, 3389, 8000]:
            res = manager.evaluate_inbound_traffic(source="10.0.0.5", port=blocked_port)
            assert res.action == "DROP", f"Port {blocked_port} should be dropped for inbound"
            assert not res.is_allowed

    # -------------------------------------------------------------------------
    # Hyper-V Port ACL script generator
    # -------------------------------------------------------------------------
    def test_hyperv_port_acl_generation(self):
        """Generate PowerShell Add-VMNetworkAdapterAcl commands for Hyper-V vSwitch enforcement."""
        acls = generate_hyperv_port_acls(vm_name="mxc-session-worker-01")
        assert len(acls) > 0

        # Verify default-deny outbound
        assert any("Deny" in cmd and "Outbound" in cmd for cmd in acls)
        # Verify default-deny inbound
        assert any("Deny" in cmd and "Inbound" in cmd for cmd in acls)

        # Verify allowed ports are present
        for port in [53, 88, 443, 1433, 5432]:
            assert any(str(port) in cmd and "Outbound" in cmd and "Allow" in cmd for cmd in acls), (
                f"Missing Hyper-V ACL rule for outbound port {port}"
            )
        # Inbound 8080 present
        assert any("8080" in cmd and "Inbound" in cmd and "Allow" in cmd for cmd in acls)
