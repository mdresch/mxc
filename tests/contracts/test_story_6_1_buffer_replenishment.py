"""Contract tests for Story 6.1 — Buffer replenishment (WBS 7.1).

Acceptance Criteria:
- AC1: Given K_min met, when a guest is leased, then another reaches StandbyPaused
       in about 1.5 s in background without blocking in-flight request (AC-05.1).
- AC2: Given pool with zero available guests, when lease requested, handle gracefully
       without crash (e.g. wait or provision on-demand / structured error).
- Invariants: States run ColdProvisioned (0 MB host RAM) -> StandbyPaused (1.0-1.2 GB) -> ActiveRunning.
"""

import pytest
import time
from scripts.lib.watermark_pool import (
    WatermarkPoolManager,
    PoolInstanceState,
    PoolConfig,
    PoolExhaustedError,
)


class TestStory61BufferReplenishment:
    """Validate watermark pool buffer replenishment and non-blocking background promotion."""

    @pytest.fixture
    def pool(self):
        config = PoolConfig(
            min_ready_standby=1,
            max_ready_standby=5,
            refill_target_seconds=1.5,
            cold_inventory_count=3,
        )
        return WatermarkPoolManager(config=config)

    # -------------------------------------------------------------------------
    # Initial State: K_min met and inventory verified
    # -------------------------------------------------------------------------
    def test_pool_initialization_kmin_met(self, pool):
        """Pool starts with K_min guests in StandbyPaused and inventory in ColdProvisioned."""
        ready = pool.get_ready_standby_guests()
        assert len(ready) == 1
        assert ready[0].state == PoolInstanceState.STANDBY_PAUSED
        assert 1024.0 <= ready[0].host_ram_mb <= 1228.8

        cold = pool.get_cold_inventory_guests()
        assert len(cold) >= 2
        for guest in cold:
            assert guest.state == PoolInstanceState.COLD_PROVISIONED
            assert guest.host_ram_mb == 0.0, "ColdProvisioned inventory must consume 0 MB host RAM"

    # -------------------------------------------------------------------------
    # AC1: Lease returns immediately & background replenishment refills in ~1.5 s
    # -------------------------------------------------------------------------
    def test_lease_promotes_next_guest_in_background(self, pool):
        """AC1 (AC-05.1): Leasing ready guest returns immediately; background worker refills in ~1.5 s."""
        start_time = time.monotonic()
        leased_guest = pool.lease_guest(session_id="sess-caller-01")
        lease_duration = time.monotonic() - start_time

        # Verify non-blocking lease
        assert lease_duration < 0.1, "Lease must not block in-flight caller"
        assert leased_guest.state == PoolInstanceState.ACTIVE_RUNNING
        assert leased_guest.session_id == "sess-caller-01"

        # Immediately after lease, ready pool momentarily drops
        # Background worker completes promotion to replenish K_min
        replenish_record = pool.await_background_replenishment(timeout_seconds=2.0)
        assert replenish_record.is_replenished
        assert replenish_record.promoted_vm_name is not None
        assert replenish_record.elapsed_seconds <= 1.8, "Refill must take about 1.5 s (<= 1.8 s)"

        # Verify ready count is restored to K_min
        ready_after = pool.get_ready_standby_guests()
        assert len(ready_after) >= 1
        assert ready_after[0].state == PoolInstanceState.STANDBY_PAUSED

    # -------------------------------------------------------------------------
    # AC2: Zero ready guests handled gracefully
    # -------------------------------------------------------------------------
    def test_zero_ready_guests_handled_gracefully(self):
        """AC2: Graceful behavior when ready pool is exhausted."""
        empty_pool = WatermarkPoolManager(
            config=PoolConfig(min_ready_standby=0, max_ready_standby=5, cold_inventory_count=0)
        )
        assert len(empty_pool.get_ready_standby_guests()) == 0

        # When non-blocking on-demand is False, raise structured PoolExhaustedError
        with pytest.raises(PoolExhaustedError) as exc_info:
            empty_pool.lease_guest(session_id="sess-overflow", allow_on_demand=False)
        assert "exhausted" in str(exc_info.value).lower()

        # When allow_on_demand is True, provision on demand without crash
        provisioned = empty_pool.lease_guest(session_id="sess-demand", allow_on_demand=True)
        assert provisioned is not None
        assert provisioned.state == PoolInstanceState.ACTIVE_RUNNING
