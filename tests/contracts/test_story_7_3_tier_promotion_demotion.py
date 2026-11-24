"""Contract test for Story 7.3: Dynamic Tier Promotion & Demotion Lifecycle (WBS 8.3).

Governed by ADR-009 (TP-07), BRD-007 (BRU-007-04..05), FDD-007 (§1.3, §2.2),
and Epic 007 Story 7.3 (AC-7.3.1, AC-7.3.2).

Contract Interpretations (from scripts/spec_gate.py 7.3):
  I1: Promotion of ColdSaved to WarmPaused executes asynchronously/background without blocking in-flight requests.
  I2: Promotion elevates instance host RAM from 0.0 MB to 1024.0-1228.8 MB with 0.0% CPU.
  I3: Idle WarmPaused instances exceeding threshold (>= 600 s) demote to ColdSaved, freeing host RAM to 0.0 MB.
  I4: Demotion strictly preserves minimum ready warm threshold unless forced by host memory pressure.
"""

import time
import pytest
from scripts.lib.watermark_pool import (
    PoolConfig,
    PoolGuestRecord,
    PoolInstanceState,
    WatermarkPoolManager,
)


def test_ac_7_3_1_background_promotion_cold_to_warm():
    """AC-7.3.1: Promotion of ColdSaved to WarmPaused completes in background without blocking in-flight requests."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    # Setup cold instance with 0.0 MB RAM
    cold_vm = manager.register_cold_saved_instance(
        vm_name="vm-cold-promote",
        checkpoint_path="C:\\hyperv\\checkpoints\\vm-cold-promote.vmrs",
    )
    assert cold_vm.state == PoolInstanceState.COLD_SAVED
    assert cold_vm.host_ram_mb == 0.0

    # Execute background promotion
    start_time = time.perf_counter()
    promoted_vm, promotion_duration = manager.promote_cold_to_warm(vm_name="vm-cold-promote")
    elapsed_total = time.perf_counter() - start_time

    assert promoted_vm.vm_name == "vm-cold-promote"
    assert promoted_vm.state == PoolInstanceState.WARM_PAUSED
    assert 1024.0 <= promoted_vm.host_ram_mb <= 1228.8
    assert promoted_vm.cpu_percent == 0.0
    assert promotion_duration <= 2.5
    assert elapsed_total <= 0.1  # Non-blocking invocation verification


def test_ac_7_3_2_idle_warm_demotion_to_cold():
    """AC-7.3.2: Instances exceeding the idle threshold (>= 600 s) in WarmPaused automatically demote and release RAM."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0, idle_demotion_seconds=600.0)
    manager = WatermarkPoolManager(config=config)

    now = time.time()

    # 1st instance: idle 650s (eligible for demotion)
    inst1 = manager.register_warm_paused_instance(vm_name="vm-warm-idle", host_ram_mb=1152.0)
    inst1.last_active_timestamp = now - 650.0

    # 2nd instance: active recently (idle only 120s, not eligible)
    inst2 = manager.register_warm_paused_instance(vm_name="vm-warm-active", host_ram_mb=1152.0)
    inst2.last_active_timestamp = now - 120.0

    assert manager.get_total_host_ram_mb() == 2304.0

    # Execute idle demotion check
    demoted_records = manager.demote_idle_warm_instances(
        idle_threshold_seconds=600.0,
        now_ts=now,
    )

    assert len(demoted_records) == 1
    vm_name, reclaimed_ram = demoted_records[0]
    assert vm_name == "vm-warm-idle"
    assert reclaimed_ram == 1152.0

    # Verify state transition and memory release
    assert inst1.state == PoolInstanceState.COLD_SAVED
    assert inst1.host_ram_mb == 0.0

    # Verify active instance stayed in WarmPaused
    assert inst2.state == PoolInstanceState.WARM_PAUSED
    assert inst2.host_ram_mb == 1152.0

    # Net host RAM drops by exactly 1152 MB
    assert manager.get_total_host_ram_mb() == 1152.0


def test_dynamic_lifecycle_round_trip():
    """Verifies complete cycle: ColdSaved -> WarmPaused -> ActiveLeased -> WarmPaused -> ColdSaved."""
    config = PoolConfig(min_ready_standby=0, cold_inventory_count=0)
    manager = WatermarkPoolManager(config=config)

    # 1. ColdSaved (0 MB RAM)
    vm = manager.register_cold_saved_instance(vm_name="vm-cycle", checkpoint_path="cycle.vmrs")
    assert vm.host_ram_mb == 0.0

    # 2. Promote to WarmPaused (1024-1228 MB RAM)
    promoted, _ = manager.promote_cold_to_warm("vm-cycle")
    assert promoted.state == PoolInstanceState.WARM_PAUSED
    assert promoted.host_ram_mb > 0.0

    # 3. Lease for session (ActiveRunning)
    leased, _, _ = manager.lease_instance_tiered(tier="gold", session_id="sess-cycle-1")
    assert leased.state == PoolInstanceState.ACTIVE_RUNNING

    # 4. Release session back to WarmPaused
    leased.state = PoolInstanceState.WARM_PAUSED
    leased.session_id = None
    leased.last_active_timestamp = 1000.0  # Simulated past timestamp

    # 5. Demote on idle timeout back to ColdSaved (0 MB RAM)
    manager.demote_idle_warm_instances(idle_threshold_seconds=600.0, now_ts=2000.0)
    assert vm.state == PoolInstanceState.COLD_SAVED
    assert vm.host_ram_mb == 0.0
