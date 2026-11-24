"""Contract tests for Story 6.4 — Scale down (WBS 7.4).

Acceptance Criteria:
- AC1: Given traffic normalized, when idle exceeds configured cooldown (record 180 s or 300 s),
       then surplus above K_min is reaped (AC-05.4).
- AC2: Given pool count at or below K_min, when cooldown fires,
       then no instances below K_min are reaped.
- Telemetry: Verify check records configured cooldown figure (180 s vs 300 s).
- Invariant: Instances with open active requests are not reaped until idle.
"""

import pytest
from scripts.lib.watermark_pool import (
    WatermarkPoolManager,
    PoolConfig,
    PoolInstanceState,
    ScaleDownResult,
    audit_cooldown_reaping,
)


class TestStory64ScaleDown:
    """Validate surplus standby scale down after cooldown and protection of K_min."""

    @pytest.fixture
    def pool_180s(self):
        config = PoolConfig(
            min_ready_standby=1,
            max_ready_standby=5,
            cooldown_seconds=180.0,
            configured_cooldown_figure="180s",
            cold_inventory_count=5,
        )
        return WatermarkPoolManager(config=config)

    @pytest.fixture
    def pool_300s(self):
        config = PoolConfig(
            min_ready_standby=2,
            max_ready_standby=6,
            cooldown_seconds=300.0,
            configured_cooldown_figure="300s",
            cold_inventory_count=5,
        )
        return WatermarkPoolManager(config=config)

    # -------------------------------------------------------------------------
    # AC1: Idle surplus above K_min reaped when cooldown exceeded
    # -------------------------------------------------------------------------
    def test_surplus_above_kmin_reaped_after_180s_cooldown(self, pool_180s):
        """AC1 (AC-05.4): Surge pool of 5 ready guests cools down to K_min (1) after 180s idle."""
        # Surge expands ready pool to 5
        pool_180s.evaluate_surge(request_rate_rps=15.0)
        assert len(pool_180s.get_ready_standby_guests()) == 5

        # Under threshold (e.g. 100s idle < 180s), 0 reaped
        res_early = pool_180s.reap_idle_surplus(idle_duration_seconds=100.0)
        assert res_early.instances_reaped == 0
        assert res_early.remaining_ready == 5

        # Exceeds cooldown (190s >= 180s), surplus of 4 reaped
        res_cool = pool_180s.reap_idle_surplus(idle_duration_seconds=190.0)
        assert res_cool.instances_reaped == 4
        assert res_cool.remaining_ready == 1
        assert len(pool_180s.get_ready_standby_guests()) == 1

    def test_300s_configured_cooldown_figure(self, pool_300s):
        """AC1 & BEN-09: Telemetry records 300s figure and cools to K_min (2)."""
        assert pool_300s.config.configured_cooldown_figure == "300s"
        assert pool_300s.config.cooldown_seconds == 300.0

        # Pre-warm to 6
        pool_300s.pre_warm_pool(target_count=6)
        assert len(pool_300s.get_ready_standby_guests()) == 6

        # Idle 310s >= 300s, reaps surplus (6 - 2 = 4 reaped)
        res = pool_300s.reap_idle_surplus(idle_duration_seconds=310.0)
        assert res.instances_reaped == 4
        assert res.remaining_ready == 2
        assert len(pool_300s.get_ready_standby_guests()) == 2

    # -------------------------------------------------------------------------
    # AC2: Instances at or below K_min are never reaped
    # -------------------------------------------------------------------------
    def test_no_reaping_when_at_kmin(self, pool_180s):
        """AC2: When pool is already at K_min (1), cooldown trigger reaps 0 instances."""
        assert len(pool_180s.get_ready_standby_guests()) == 1

        # Idle 1000s
        res = pool_180s.reap_idle_surplus(idle_duration_seconds=1000.0)
        assert res.instances_reaped == 0
        assert res.remaining_ready == 1
        assert len(pool_180s.get_ready_standby_guests()) == 1

    def test_no_reaping_when_below_kmin(self, pool_300s):
        """AC2: If ready pool is below K_min (e.g. 1 out of 2), cooldown never reaps."""
        # Lease one guest so ready is 1 (below K_min=2)
        pool_300s.lease_guest(session_id="sess-active-01")
        # Ensure remaining ready is <= K_min
        ready_count = len(pool_300s.get_ready_standby_guests())
        assert ready_count <= pool_300s.config.min_ready_standby

        res = pool_300s.reap_idle_surplus(idle_duration_seconds=500.0)
        assert res.instances_reaped == 0
        assert res.remaining_ready == ready_count

    # -------------------------------------------------------------------------
    # Telemetry Audit Helper
    # -------------------------------------------------------------------------
    def test_audit_cooldown_reaping_helper(self, pool_180s):
        """Verify audit helper records configured cooldown figure and target K_min."""
        pool_180s.evaluate_surge(request_rate_rps=12.0)
        audit_payload = audit_cooldown_reaping(pool_180s, idle_duration_seconds=200.0)
        assert audit_payload["configured_figure"] == "180s"
        assert audit_payload["cooldown_seconds"] == 180.0
        assert audit_payload["k_min"] == 1
        assert audit_payload["reaped_count"] == 4
        assert audit_payload["remaining_count"] == 1
