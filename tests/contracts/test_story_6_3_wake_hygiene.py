"""Contract tests for Story 6.3 — Wake hygiene (WBS 7.3).

Acceptance Criteria:
- AC1: Given restore from baseline-hot-ready, when /health first succeeds,
       then entropy reseeded, clock synced within 50 ms host UTC, and DB pools cleared (AC-02.4).
- AC2: Given wake failure during hygiene sequence, then instance is quarantined/reaped
       and not routed traffic (raises WakeHygieneError).

Interpretations:
- [I1] Empty Collection Base Case:
       Passing zero records or an empty sequence to batch wake hygiene must return
       an empty result without raising an error.
"""

import pytest
from scripts.lib.watermark_pool import (
    WatermarkPoolManager,
    PoolConfig,
    PoolInstanceState,
    WakeHygieneError,
    WakeHygieneResult,
    verify_health_endpoint,
    batch_wake_hygiene,
)


class TestStory63WakeHygiene:
    """Validate 3-step wake hygiene (/health), quarantine on failure, and empty base case."""

    @pytest.fixture
    def pool(self):
        config = PoolConfig(min_ready_standby=1, max_ready_standby=5)
        return WatermarkPoolManager(config=config)

    # -------------------------------------------------------------------------
    # AC1: Successful 3-step wake hygiene on /health
    # -------------------------------------------------------------------------
    def test_successful_wake_hygiene_sequence(self, pool):
        """AC1 (AC-02.4): All three steps pass before instance accepts traffic."""
        vm = pool.get_ready_standby_guests()[0]

        result: WakeHygieneResult = pool.perform_wake_hygiene(
            vm_name=vm.vm_name,
            clock_drift_ms=14.5,
            simulated_entropy_ok=True,
            simulated_clock_ok=True,
            simulated_pool_ok=True,
        )

        assert result.is_healthy is True
        assert result.entropy_reseeded is True
        assert result.clock_drift_ms == 14.5
        assert result.clock_drift_ms <= 50.0
        assert result.db_pools_flushed == 0
        assert "Entropy reseeded" in result.details
        assert vm.state == PoolInstanceState.STANDBY_PAUSED

    def test_verify_health_endpoint_helper(self, pool):
        """Verify /health helper reports 200 OK only when hygiene passes."""
        vm = pool.get_ready_standby_guests()[0]
        status_code, payload = verify_health_endpoint(pool, vm.vm_name, clock_drift_ms=8.0)
        assert status_code == 200
        assert payload["status"] == "UP"
        assert payload["entropy"] == "RESEEDED"
        assert payload["clock_synced"] is True
        assert payload["db_pools"] == "CLEARED"

    # -------------------------------------------------------------------------
    # AC2: Wake failure quarantines instance and denies traffic
    # -------------------------------------------------------------------------
    def test_entropy_failure_quarantines_instance(self, pool):
        """AC2: Entropy reseed failure raises WakeHygieneError and marks instance Quarantined."""
        vm = pool.get_ready_standby_guests()[0]
        with pytest.raises(WakeHygieneError) as exc_info:
            pool.perform_wake_hygiene(vm.vm_name, simulated_entropy_ok=False)
        assert "entropy=False" in str(exc_info.value)
        assert vm.state == PoolInstanceState.QUARANTINED

    def test_excessive_clock_drift_quarantines_instance(self, pool):
        """AC2: Clock drift > 50 ms fails hygiene and quarantines instance."""
        vm = pool.get_ready_standby_guests()[0]
        with pytest.raises(WakeHygieneError) as exc_info:
            pool.perform_wake_hygiene(vm.vm_name, clock_drift_ms=75.0)  # > 50 ms
        assert "clock=False" in str(exc_info.value)
        assert vm.state == PoolInstanceState.QUARANTINED

    def test_unclosed_db_pool_handles_quarantines_instance(self, pool):
        """AC2: Lingering DB connection pool handles fail hygiene and quarantine instance."""
        vm = pool.get_ready_standby_guests()[0]
        with pytest.raises(WakeHygieneError) as exc_info:
            pool.perform_wake_hygiene(vm.vm_name, simulated_pool_ok=False)
        assert "db_pools=False" in str(exc_info.value)
        assert vm.state == PoolInstanceState.QUARANTINED

    def test_health_endpoint_returns_503_on_hygiene_failure(self, pool):
        """/health probe returns HTTP 503 Service Unavailable when hygiene fails."""
        vm = pool.get_ready_standby_guests()[0]
        status_code, payload = verify_health_endpoint(pool, vm.vm_name, clock_drift_ms=120.0)
        assert status_code == 503
        assert payload["status"] == "DOWN"
        assert "quarantined" in payload["error"].lower()

    # -------------------------------------------------------------------------
    # Interpretation I1: Empty collection base case
    # -------------------------------------------------------------------------
    def test_batch_wake_hygiene_empty_collection(self, pool):
        """I1: Passing empty sequence to batch wake hygiene returns empty dict without error."""
        results = batch_wake_hygiene(pool, [])
        assert results == {}
