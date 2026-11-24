"""Contract test for Story 8.1: Early TLS ClientHello SNI Snooper (WBS 9.1).

Governed by ADR-010 (TP-08), BRD-008 (BRU-008-01..02), FDD-008 (§1.1, §1.2),
and Epic 008 Story 8.1 (AC-8.1.1, AC-8.1.2).

Contract Interpretations (from scripts/spec_gate.py 8.1):
  I1: Non-blocking binary TLS parser extracts Server Name Indication (SNI) in <= 5.0 ms.
  I2: Parser defensively rejects non-TLS, malformed, or plain HTTP frames without exceptions.
  I3: Asynchronous wake signal dispatches to the pool manager concurrently before TLS handshake completion.
  I4: Pre-wake event accurately associates target tenant host with appropriate pool instance.
"""

import time
import pytest
from scripts.lib.watermark_pool import PoolConfig, PoolInstanceState, WatermarkPoolManager
from scripts.lib.tls_snooper import (
    TLSSnooper,
    build_test_client_hello,
    parse_tls_sni,
)


def test_ac_8_1_1_binary_sni_parsing_sub_5ms():
    """AC-8.1.1: Non-blocking TLS parser extracts SNI within <= 5 ms of TCP connection receipt."""
    target_host = "tenant-adpa.mxc.internal"
    client_hello_bytes = build_test_client_hello(target_host)

    start_time = time.perf_counter()
    extracted_host = parse_tls_sni(client_hello_bytes)
    parse_elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert extracted_host == target_host
    # Performance assertion: parse latency <= 5.0 ms (AC-8.1.1)
    assert parse_elapsed_ms <= 5.0


def test_ac_8_1_2_async_wake_dispatched_before_handshake():
    """AC-8.1.2: Asynchronous wake signal dispatched to pool manager before TLS session key exchange completes."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    # Register cold saved tenant instance
    cold_vm = manager.register_cold_saved_instance(
        vm_name="vm-tenant-alpha",
        checkpoint_path="C:\\hyperv\\checkpoints\\vm-tenant-alpha.vmrs",
    )
    assert cold_vm.state == PoolInstanceState.COLD_SAVED

    # Map SNI host to VM
    tenant_map = {"alpha.mxc.internal": "vm-tenant-alpha"}
    snooper = TLSSnooper(pool_manager=manager, tenant_vm_map=tenant_map)

    packet = build_test_client_hello("alpha.mxc.internal")

    # Intercept frame and dispatch pre-wake
    start_time = time.perf_counter()
    sni_host, wake_dispatched, latency_ms = snooper.snoop_and_pre_wake(packet)
    total_invocation_ms = (time.perf_counter() - start_time) * 1000.0

    assert sni_host == "alpha.mxc.internal"
    assert wake_dispatched is True
    assert latency_ms <= 5.0
    assert total_invocation_ms <= 10.0  # Asynchronous dispatch does not block caller

    # Verify instance was promoted/pre-warmed to WarmPaused
    assert cold_vm.state == PoolInstanceState.WARM_PAUSED
    assert cold_vm.host_ram_mb > 0.0


def test_defensive_rejection_of_non_tls_traffic():
    """Verifies that non-TLS, truncated, or plain HTTP frames return None without raising exceptions."""
    # Plain HTTP GET
    http_packet = b"GET /api/v1/health HTTP/1.1\r\nHost: example.com\r\n\r\n"
    assert parse_tls_sni(http_packet) is None

    # Garbage binary frame
    garbage = b"\x00\x01\x02\x03\x04\x05"
    assert parse_tls_sni(garbage) is None

    # Truncated TLS header
    truncated = b"\x16\x03\x01"
    assert parse_tls_sni(truncated) is None

    # Empty payload
    assert parse_tls_sni(b"") is None


def test_unknown_sni_bypasses_pre_wake():
    """Verifies that an unmapped SNI host does not dispatch invalid wake events."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)
    snooper = TLSSnooper(pool_manager=manager, tenant_vm_map={})

    packet = build_test_client_hello("unknown.tenant.io")
    sni_host, wake_dispatched, latency_ms = snooper.snoop_and_pre_wake(packet)

    assert sni_host == "unknown.tenant.io"
    assert wake_dispatched is False
    assert latency_ms <= 5.0
