"""Contract test for Story 7.1: Three-Tier State Management & Inventory (WBS 8.1).

Governed by ADR-009 (TP-07), BRD-007 (BRU-007-01..02), FDD-007 (§1.1..1.3),
and Epic 007 Story 7.1 (AC-7.1.1, AC-7.1.2, AC-7.1.3).

Contract Interpretations (from scripts/spec_gate.py 7.1):
  I1: ColdSaved instances occupy exactly 0.0 MB host RAM and point to a saved checkpoint disk path.
  I2: WarmPaused instances occupy 1024.0 - 1228.8 MB host RAM while consuming 0.0% CPU.
  I3: HotRunning instances execute in an idle loop and dispatch to incoming leases in <= 5.0 ms.
  I4: Pool manager provides structured inventory breakdown across Hot, Warm, and Cold tiers.
"""

import time
import pytest
from scripts.lib.watermark_pool import (
    PoolConfig,
    PoolGuestRecord,
    PoolInstanceState,
    WatermarkPoolManager,
)


def test_ac_7_1_1_cold_saved_zero_ram_checkpoint():
    """AC-7.1.1: ColdSaved instances occupy 0.0 MB host RAM and reside as saved state disk checkpoints."""
    config = PoolConfig(
        min_ready_standby=1,
        max_ready_standby=5,
        cold_saved_inventory_count=10,
    )
    manager = WatermarkPoolManager(config=config)

    # Register and verify cold saved instance
    cold_vm = manager.register_cold_saved_instance(
        vm_name="vm-cold-001",
        checkpoint_path="C:\\hyperv\\checkpoints\\vm-cold-001.vmrs",
    )

    assert cold_vm.state == PoolInstanceState.COLD_SAVED
    assert cold_vm.host_ram_mb == 0.0
    assert cold_vm.checkpoint_path == "C:\\hyperv\\checkpoints\\vm-cold-001.vmrs"
    assert cold_vm.cpu_percent == 0.0

    # Ensure aggregate host RAM from 10 ColdSaved instances is strictly 0.0 MB
    for i in range(2, 11):
        manager.register_cold_saved_instance(
            vm_name=f"vm-cold-{i:03d}",
            checkpoint_path=f"C:\\hyperv\\checkpoints\\vm-cold-{i:03d}.vmrs",
        )

    cold_instances = manager.get_cold_saved_instances()
    assert len(cold_instances) == 10
    total_cold_ram = sum(inst.host_ram_mb for inst in cold_instances)
    assert total_cold_ram == 0.0


def test_ac_7_1_2_warm_paused_footprint_and_idle_cpu():
    """AC-7.1.2: WarmPaused instances occupy 1024-1228 MB host RAM at 0.0% CPU."""
    config = PoolConfig(
        min_ready_standby=2,
        max_ready_standby=5,
    )
    manager = WatermarkPoolManager(config=config)

    # Register warm paused instance
    warm_vm = manager.register_warm_paused_instance(
        vm_name="vm-warm-001",
        host_ram_mb=1152.0,
    )

    assert warm_vm.state == PoolInstanceState.WARM_PAUSED
    assert 1024.0 <= warm_vm.host_ram_mb <= 1228.8
    assert warm_vm.cpu_percent == 0.0

    # Verify inventory filter
    warm_instances = manager.get_warm_paused_instances()
    assert len(warm_instances) >= 1
    assert any(inst.vm_name == "vm-warm-001" for inst in warm_instances)


def test_ac_7_1_3_hot_running_dispatch_sub_5ms():
    """AC-7.1.3: HotRunning instances execute in idle wait state with dispatch latency <= 5 ms."""
    config = PoolConfig(
        min_ready_standby=1,
        max_ready_standby=5,
    )
    manager = WatermarkPoolManager(config=config)

    manager.register_hot_running_instance(
        vm_name="vm-hot-001",
        host_ram_mb=1024.0,
    )

    hot_instances = manager.get_hot_running_instances()
    assert len(hot_instances) == 1

    # Lease hot instance and measure dispatch latency
    start_time = time.perf_counter()
    leased_instance, dispatch_latency_ms = manager.lease_hot_instance(session_id="sess-platinum-101")
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert leased_instance.vm_name == "vm-hot-001"
    assert leased_instance.state in (PoolInstanceState.ACTIVE_RUNNING, PoolInstanceState.ACTIVE_LEASED)
    assert leased_instance.session_id == "sess-platinum-101"
    # Verification of dispatch latency benchmark <= 5.0 ms (AC-7.1.3)
    assert dispatch_latency_ms <= 5.0
    assert elapsed_ms <= 15.0  # Execution overhead bound


def test_three_tier_inventory_breakdown_and_ram_accounting():
    """Verifies complete multi-tier inventory accounting and host RAM calculation."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    # 1 Hot (1024 MB), 2 Warm (1024 MB each), 5 Cold (0 MB each)
    manager.register_hot_running_instance(vm_name="vm-hot-1", host_ram_mb=1024.0)
    manager.register_warm_paused_instance(vm_name="vm-warm-1", host_ram_mb=1024.0)
    manager.register_warm_paused_instance(vm_name="vm-warm-2", host_ram_mb=1024.0)
    for i in range(1, 6):
        manager.register_cold_saved_instance(vm_name=f"vm-cold-{i}", checkpoint_path=f"disk-{i}.vmrs")

    breakdown = manager.get_tier_breakdown()
    assert breakdown["hot"] == 1
    assert breakdown["warm"] == 2
    assert breakdown["cold"] == 5
    assert breakdown["total"] == 8

    # Host RAM should reflect only hot + warm = 3072.0 MB
    assert manager.get_total_host_ram_mb() == 3072.0
