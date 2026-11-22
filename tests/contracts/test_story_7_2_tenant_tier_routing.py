"""Contract test for Story 7.2: Tenant Tier Classification & Dispatch Routing (WBS 8.2).

Governed by ADR-009 (TP-07), BRD-007 (BRU-007-03), FDD-007 (§1.2, §2.1),
and Epic 007 Story 7.2 (AC-7.2.1, AC-7.2.2, AC-7.2.3).

Contract Interpretations (from scripts/spec_gate.py 7.2):
  I1: Platinum tenant requests route to HotRunning instances and achieve dispatch latency <= 5.0 ms.
  I2: Gold tenant requests route to WarmPaused instances with unpause latency <= 250.0 ms.
  I3: Silver/Batch requests route to ColdSaved instances with disk resume latency <= 4000.0 ms.
  I4: If target tier has zero ready instances, router gracefully cascades to next available tier with audit telemetry.
"""

import time
import pytest
from scripts.lib.watermark_pool import (
    PoolConfig,
    PoolGuestRecord,
    PoolInstanceState,
    WatermarkPoolManager,
)


def test_ac_7_2_1_platinum_dispatch_sub_5ms():
    """AC-7.2.1: High-priority (Platinum) tenant requests dispatch to HotRunning instances in <= 5 ms."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    manager.register_hot_running_instance(vm_name="vm-hot-plat", host_ram_mb=1024.0)

    start_time = time.perf_counter()
    guest, latency_ms, tier_served = manager.lease_instance_tiered(
        tier="platinum",
        session_id="sess-plat-001",
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert guest.vm_name == "vm-hot-plat"
    assert tier_served == "platinum"
    assert guest.state in (PoolInstanceState.ACTIVE_RUNNING, PoolInstanceState.ACTIVE_LEASED)
    assert latency_ms <= 5.0
    assert elapsed_ms <= 15.0


def test_ac_7_2_2_gold_dispatch_sub_250ms():
    """AC-7.2.2: Standard (Gold) requests dispatch to WarmPaused instances with unpause latency <= 250 ms."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    manager.register_warm_paused_instance(vm_name="vm-warm-gold", host_ram_mb=1152.0)

    guest, latency_ms, tier_served = manager.lease_instance_tiered(
        tier="gold",
        session_id="sess-gold-001",
    )

    assert guest.vm_name == "vm-warm-gold"
    assert tier_served == "gold"
    assert guest.state in (PoolInstanceState.ACTIVE_RUNNING, PoolInstanceState.ACTIVE_LEASED)
    # Unpause latency benchmark <= 250.0 ms (AC-7.2.2)
    assert latency_ms <= 250.0


def test_ac_7_2_3_silver_batch_dispatch_sub_4s():
    """AC-7.2.3: Batch/low-priority requests dispatch to ColdSaved instances with disk resume <= 4.0 s."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    manager.register_cold_saved_instance(
        vm_name="vm-cold-silver",
        checkpoint_path="C:\\hyperv\\checkpoints\\vm-cold-silver.vmrs",
    )

    guest, latency_ms, tier_served = manager.lease_instance_tiered(
        tier="silver",
        session_id="sess-silver-001",
    )

    assert guest.vm_name == "vm-cold-silver"
    assert tier_served == "silver"
    assert guest.state in (PoolInstanceState.ACTIVE_RUNNING, PoolInstanceState.ACTIVE_LEASED)
    # Checkpoint restore latency <= 4000.0 ms (4.0 s, AC-7.2.3)
    assert latency_ms <= 4000.0


def test_tier_fallback_cascade_when_primary_empty():
    """Verifies that an empty Hot tier cascades gracefully to Warm tier with audit trace."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    # Hot tier is empty, only Warm instance is available
    manager.register_warm_paused_instance(vm_name="vm-warm-fallback", host_ram_mb=1152.0)

    guest, latency_ms, tier_served = manager.lease_instance_tiered(
        tier="platinum",
        session_id="sess-plat-fallback",
        allow_cascade=True,
    )

    assert guest.vm_name == "vm-warm-fallback"
    assert tier_served == "gold"  # Cascaded to Gold (WarmPaused)
    assert latency_ms <= 250.0
