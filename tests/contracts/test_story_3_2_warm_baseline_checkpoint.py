"""Contract test for Story 3.2: Warm baseline checkpoint capture.

Governed by ADR-003, BRD-003 (BRU-003-03), FDD-003, and WBS 4.2.
Enforces AC-04.2:
- Given bake completes, when service answers smoke on `localhost:8080/health`,
  then DB handles are closed and `baseline-hot-ready` is captured.
- Avoids JIT compilation stall on first wake from the checkpoint.
"""

from __future__ import annotations

import time
import pytest

from scripts.lib.production_image import (
    BakeCheckpointError,
    BakeHealthSmokeResult,
    CheckpointMetadata,
    ProductionImageBakeEngine,
    ServiceHealthStatus,
    WarmCheckpointState,
)


class TestStory32WarmBaselineCheckpoint:
    """Acceptance contract suite for AC-04.2 / Story 3.2."""

    def test_warm_baseline_checkpoint_success_sequence(self) -> None:
        """AC-04.2 / BRU-003-03: Complete smoke, close DB handles, capture baseline-hot-ready."""
        engine = ProductionImageBakeEngine(vm_name="MXC-Bake-Prod-Temp")

        # 1. Simulate service startup and successful health smoke on :8080/health
        smoke_result = engine.probe_health_smoke(
            endpoint_url="http://localhost:8080/health",
            response_payload={
                "status": "ok",
                "entropy_source": "sys_cng",
                "clock_synced": True,
            },
            status_code=200,
        )
        assert smoke_result.status == ServiceHealthStatus.HEALTHY
        assert smoke_result.is_smoke_passed is True

        # 2. Flush and close database handles
        db_flush = engine.flush_and_close_db_handles(open_handles_before=3)
        assert db_flush.closed_handles_count == 3
        assert db_flush.active_handles_remaining == 0

        # 3. Capture baseline-hot-ready checkpoint
        checkpoint = engine.capture_warm_checkpoint(
            checkpoint_name="baseline-hot-ready",
            smoke_result=smoke_result,
            db_flush_result=db_flush,
        )

        assert checkpoint.checkpoint_name == "baseline-hot-ready"
        assert checkpoint.state == WarmCheckpointState.HOT_READY
        assert checkpoint.db_handles_closed is True
        assert checkpoint.smoke_verified is True
        assert checkpoint.captured_at > 0

    def test_warm_baseline_checkpoint_fails_if_smoke_probe_fails(self) -> None:
        """AC-04.2: If service smoke test fails or times out, checkpoint capture is aborted."""
        engine = ProductionImageBakeEngine(vm_name="MXC-Bake-Prod-Temp")

        smoke_result = engine.probe_health_smoke(
            endpoint_url="http://localhost:8080/health",
            response_payload={"status": "degraded", "error": "JIT initialization incomplete"},
            status_code=500,
        )
        assert smoke_result.is_smoke_passed is False

        db_flush = engine.flush_and_close_db_handles(open_handles_before=0)

        with pytest.raises(BakeCheckpointError) as exc_info:
            engine.capture_warm_checkpoint(
                checkpoint_name="baseline-hot-ready",
                smoke_result=smoke_result,
                db_flush_result=db_flush,
            )

        assert "smoke" in str(exc_info.value).lower()
        assert "health" in str(exc_info.value).lower()

    def test_warm_baseline_checkpoint_fails_if_db_handles_unclosed(self) -> None:
        """AC-04.2 / BRU-003-03: Abort checkpoint if active database handles remain open."""
        engine = ProductionImageBakeEngine(vm_name="MXC-Bake-Prod-Temp")

        smoke_result = engine.probe_health_smoke(
            endpoint_url="http://localhost:8080/health",
            response_payload={"status": "healthy"},
            status_code=200,
        )

        # Incomplete flush leaves handles open
        db_flush = engine.simulate_incomplete_db_flush(remaining_handles=2)

        with pytest.raises(BakeCheckpointError) as exc_info:
            engine.capture_warm_checkpoint(
                checkpoint_name="baseline-hot-ready",
                smoke_result=smoke_result,
                db_flush_result=db_flush,
            )

        assert "db" in str(exc_info.value).lower() or "database" in str(exc_info.value).lower()
        assert "BRU-003-03" in str(exc_info.value)

    def test_checkpoint_name_must_be_baseline_hot_ready(self) -> None:
        """ADR-003 §4.4: Checkpoint name must strictly be 'baseline-hot-ready'."""
        engine = ProductionImageBakeEngine(vm_name="MXC-Bake-Prod-Temp")

        smoke_result = engine.probe_health_smoke(
            endpoint_url="http://localhost:8080/health",
            response_payload={"status": "healthy"},
            status_code=200,
        )
        db_flush = engine.flush_and_close_db_handles(open_handles_before=1)

        with pytest.raises(BakeCheckpointError) as exc_info:
            engine.capture_warm_checkpoint(
                checkpoint_name="arbitrary-snapshot-name",
                smoke_result=smoke_result,
                db_flush_result=db_flush,
            )

        assert "baseline-hot-ready" in str(exc_info.value)

    def test_first_wake_from_hot_ready_avoids_jit_compile(self) -> None:
        """AC-04.2 / ADR-003 §4.4: Wake from baseline-hot-ready exhibits warm pre-jitted performance."""
        engine = ProductionImageBakeEngine(vm_name="MXC-Bake-Prod-Temp")

        smoke_result = engine.probe_health_smoke(
            endpoint_url="http://localhost:8080/health",
            response_payload={"status": "healthy"},
            status_code=200,
        )
        db_flush = engine.flush_and_close_db_handles(open_handles_before=0)
        checkpoint = engine.capture_warm_checkpoint(
            checkpoint_name="baseline-hot-ready",
            smoke_result=smoke_result,
            db_flush_result=db_flush,
        )

        wake_metrics = engine.simulate_wake_from_checkpoint(checkpoint)
        assert wake_metrics.jit_compile_stall_ms == 0.0
        assert wake_metrics.is_pre_warmed is True
        assert wake_metrics.ttfb_overhead_ms <= 5.0
