"""Contract tests for Story 6.2 — Surge expansion (WBS 7.2).

Acceptance Criteria:
- AC1: Given configured surge threshold (record 5 rps or 10 rps/5 s), when tripped
       or queue depth > 0, then ready count expands up to K_max (AC-05.2, BEN-09).
- AC2: Given ready count at K_max, when additional surge occurs,
       then pool does not exceed K_max ceiling.
- Telemetry: Check explicitly records which threshold was configured (5 rps vs 10 rps/5 s).
- Pre-warm command: mxc-pool-warm / pre_warm_pool expands pool ahead of time (AC-05.3).
"""

import pytest
from scripts.lib.watermark_pool import (
    WatermarkPoolManager,
    PoolConfig,
    PoolInstanceState,
    SurgeExpansionResult,
)


class TestStory62SurgeExpansion:
    """Validate velocity and queue surge expansion up to K_max and strict ceiling enforcement."""

    @pytest.fixture
    def pool_10rps(self):
        config = PoolConfig(
            min_ready_standby=1,
            max_ready_standby=5,
            surge_velocity_threshold_rps=10.0,
            configured_surge_figure="10_rps_5s",
            cold_inventory_count=5,
        )
        return WatermarkPoolManager(config=config)

    @pytest.fixture
    def pool_5rps(self):
        config = PoolConfig(
            min_ready_standby=1,
            max_ready_standby=5,
            surge_velocity_threshold_rps=5.0,
            configured_surge_figure="5_rps",
            cold_inventory_count=5,
        )
        return WatermarkPoolManager(config=config)

    # -------------------------------------------------------------------------
    # AC1: Surge threshold tripped expands ready count to K_max
    # -------------------------------------------------------------------------
    def test_velocity_surge_trips_expansion_to_kmax(self, pool_10rps):
        """AC1: Request velocity >= 10 rps expands ready count up to K_max (5)."""
        assert len(pool_10rps.get_ready_standby_guests()) == 1

        # Trip surge via 12 rps
        result: SurgeExpansionResult = pool_10rps.evaluate_surge(request_rate_rps=12.0, queue_depth=0)
        assert result.is_surge_active is True
        assert result.requested_rps == 12.0
        assert result.total_ready_count == 5
        assert result.max_kmax == 5

        # Verify pool state
        ready = pool_10rps.get_ready_standby_guests()
        assert len(ready) == 5
        for g in ready:
            assert g.state == PoolInstanceState.STANDBY_PAUSED

    def test_queue_depth_surge_trips_expansion(self, pool_10rps):
        """AC1: Queue depth > 0 trips immediate surge expansion even below velocity threshold."""
        assert len(pool_10rps.get_ready_standby_guests()) == 1

        # 2 rps but queue depth 3
        result = pool_10rps.evaluate_surge(request_rate_rps=2.0, queue_depth=3)
        assert result.is_surge_active is True
        assert result.queue_depth == 3
        assert result.total_ready_count == 5

    def test_5rps_configured_benchmark_records_telemetry(self, pool_5rps):
        """BEN-09: Telemetry records configured surge figure (5 rps vs 10 rps)."""
        assert pool_5rps.config.configured_surge_figure == "5_rps"

        # 6 rps trips 5 rps pool
        res = pool_5rps.evaluate_surge(request_rate_rps=6.0, queue_depth=0)
        assert res.is_surge_active is True
        assert res.total_ready_count == 5

    def test_normal_traffic_below_threshold_does_not_surge(self, pool_10rps):
        """Under normal traffic (below threshold, queue depth 0), pool does not surge."""
        assert len(pool_10rps.get_ready_standby_guests()) == 1

        result = pool_10rps.evaluate_surge(request_rate_rps=4.0, queue_depth=0)
        assert result.is_surge_active is False
        assert result.instances_expanded == 0
        assert result.total_ready_count == 1

    # -------------------------------------------------------------------------
    # AC2: Strict K_max ceiling enforcement
    # -------------------------------------------------------------------------
    def test_pool_does_not_exceed_kmax_ceiling(self, pool_10rps):
        """AC2: Once K_max is reached, additional surges do not expand beyond K_max."""
        # First surge expands to 5
        pool_10rps.evaluate_surge(request_rate_rps=20.0, queue_depth=5)
        assert len(pool_10rps.get_ready_standby_guests()) == 5

        # Subsequent extreme surge (50 rps, queue depth 20)
        res2 = pool_10rps.evaluate_surge(request_rate_rps=50.0, queue_depth=20)
        assert res2.is_surge_active is True
        assert res2.instances_expanded == 0, "No new instances created beyond K_max"
        assert res2.total_ready_count == 5
        assert len(pool_10rps.get_ready_standby_guests()) == 5

    # -------------------------------------------------------------------------
    # Pre-Warm Command (AC-05.3)
    # -------------------------------------------------------------------------
    def test_pre_warm_pool_command(self, pool_10rps):
        """AC-05.3: mxc-pool-warm / pre_warm_pool directly raises ready count up to target."""
        assert len(pool_10rps.get_ready_standby_guests()) == 1

        pre_warmed = pool_10rps.pre_warm_pool(target_count=3)
        assert pre_warmed == 3
        assert len(pool_10rps.get_ready_standby_guests()) == 3

        # Clamped to K_max
        pre_warmed_clamped = pool_10rps.pre_warm_pool(target_count=10)
        assert pre_warmed_clamped == 5
        assert len(pool_10rps.get_ready_standby_guests()) == 5
