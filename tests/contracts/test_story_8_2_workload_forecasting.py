"""Contract Test: Story 8.2 — Time-Series Workload Forecasting Engine (WBS 9.2).

Governing Artifacts:
- ADR: ADR-010 (Predictive Wake Interception & Activity-Based Forecasting)
- BRD: BRD-008 (BRU-008-03, BRU-008-04)
- FDD: FDD-008 (§1.3 Time-Series Activity Forecaster)
- Epic: Epic 008 (User Story 8.2, WBS 9.2)

Acceptance Criteria:
- AC-8.2.1: Time-series forecaster predicts recurring shifts and cron batches
  >= 60 seconds in advance with >= 90% accuracy.
- AC-8.2.2: Target standby instances reach WarmPaused or HotRunning before client
  requests arrive.

Adversarial Gate Interpretations:
- [I1] Defensive None-Safety: Optional fields (e.g. metadata, user_id, confidence)
  must be safely handled without AttributeError when None.
"""

from datetime import datetime, timedelta, timezone
import pytest

from scripts.lib.watermark_pool import (
    PoolConfig,
    PoolInstanceState,
    WatermarkPoolManager,
)
from scripts.lib.workload_forecaster import (
    ForecastPrediction,
    TrafficDataPoint,
    WorkloadForecaster,
)


def test_forecast_recurring_shift_and_accuracy():
    """AC-8.2.1: Forecaster predicts recurring shift >= 60s in advance with >= 90% accuracy."""
    forecaster = WorkloadForecaster(lead_time_seconds=60.0)

    # Simulate 7 days of tenant 'corp-alpha' beginning work every day at 08:55:00 UTC
    base_date = datetime(2026, 11, 10, 0, 0, 0, tzinfo=timezone.utc)
    for day in range(7):
        day_start = base_date + timedelta(days=day)
        shift_time = day_start.replace(hour=8, minute=55, second=0)
        forecaster.record_event(
            TrafficDataPoint(
                tenant_id="corp-alpha",
                timestamp=shift_time,
                request_count=25,
                metadata={"shift": "morning_start"},
            )
        )

    # Query prediction on day 8 morning at 08:50:00 UTC (5 minutes before shift)
    current_time = base_date + timedelta(days=7, hours=8, minutes=50)
    predictions = forecaster.predict_upcoming_peaks(
        current_time=current_time,
        forecast_horizon_seconds=900.0,  # 15 minutes ahead
    )

    assert len(predictions) >= 1
    alpha_pred = next((p for p in predictions if p.tenant_id == "corp-alpha"), None)
    assert alpha_pred is not None

    # Expected peak is at 08:55:00
    expected_peak = base_date + timedelta(days=7, hours=8, minutes=55)
    time_diff = abs((alpha_pred.predicted_peak_time - expected_peak).total_seconds())
    assert time_diff <= 30.0  # within 30s precision

    # Advance warning is >= 60 seconds
    advance_notice = (alpha_pred.predicted_peak_time - current_time).total_seconds()
    assert advance_notice >= 60.0

    # Recommended prewarm time is scheduled at least 60s before the predicted peak
    lead_time = (alpha_pred.predicted_peak_time - alpha_pred.recommended_prewarm_time).total_seconds()
    assert lead_time >= 60.0

    # Test accuracy evaluation >= 90%
    actual_test_events = [
        TrafficDataPoint(
            tenant_id="corp-alpha",
            timestamp=expected_peak,
            request_count=30,
        )
    ]
    accuracy = forecaster.evaluate_accuracy(
        predictions=predictions,
        actual_events=actual_test_events,
        tolerance_seconds=120.0,
    )
    assert accuracy >= 0.90


def test_forecast_recurring_cron_batch():
    """AC-8.2.1: Forecaster predicts periodic recurring cron batches (e.g. every hour on the hour)."""
    forecaster = WorkloadForecaster(lead_time_seconds=90.0)

    # Hourly cron for 'tenant-cron' over 48 hours
    start_time = datetime(2026, 11, 15, 0, 0, 0, tzinfo=timezone.utc)
    for hour in range(48):
        cron_time = start_time + timedelta(hours=hour)
        forecaster.record_event(
            TrafficDataPoint(
                tenant_id="tenant-cron",
                timestamp=cron_time,
                request_count=100,
            )
        )

    # Check prediction at 48 hours + 57 minutes (3 minutes before next hourly cron)
    eval_time = start_time + timedelta(hours=48, minutes=57)
    predictions = forecaster.predict_upcoming_peaks(
        current_time=eval_time,
        forecast_horizon_seconds=600.0,  # 10 minutes ahead
    )

    cron_pred = next((p for p in predictions if p.tenant_id == "tenant-cron"), None)
    assert cron_pred is not None
    expected_next = start_time + timedelta(hours=49)
    assert abs((cron_pred.predicted_peak_time - expected_next).total_seconds()) <= 15.0
    assert cron_pred.confidence >= 0.90


def test_target_instances_prewarmed_to_warm_or_hot():
    """AC-8.2.2: Target standby instances reach WarmPaused or HotRunning before client requests arrive."""
    pool_config = PoolConfig(
        min_ready_standby=0,
        cold_inventory_count=3,
        cold_saved_inventory_count=3,
        warm_pool_min=0,
        hot_pool_min=0,
    )
    pool = WatermarkPoolManager(pool_config)
    forecaster = WorkloadForecaster(lead_time_seconds=60.0)

    # Initial state: only cold instances exist
    breakdown = pool.get_tier_breakdown()
    assert breakdown["cold"] == 3
    assert breakdown["warm"] == 0
    assert breakdown["hot"] == 0

    target_time = datetime(2026, 11, 20, 9, 0, 0, tzinfo=timezone.utc)
    # Register prediction that peak will arrive at 09:00:00, so prewarm triggers at 08:59:00
    prediction = ForecastPrediction(
        tenant_id="vip-tenant",
        predicted_peak_time=target_time,
        recommended_prewarm_time=target_time - timedelta(seconds=60),
        confidence=0.95,
        target_tier="WarmPaused",
    )

    # Trigger pre-warm schedule at 08:59:10 (within the pre-warm window, before peak)
    check_time = target_time - timedelta(seconds=50)
    prewarmed = forecaster.trigger_prewarm_schedule(
        pool_manager=pool,
        predictions=[prediction],
        current_time=check_time,
    )

    assert len(prewarmed) >= 1
    assert prewarmed[0].tenant_id == "vip-tenant"
    assert prewarmed[0].achieved_tier in (PoolInstanceState.WARM_PAUSED, PoolInstanceState.HOT_RUNNING)

    # Verify pool state updated
    breakdown_after = pool.get_tier_breakdown()
    assert breakdown_after["warm"] >= 1 or breakdown_after["hot"] >= 1
    assert breakdown_after["cold"] < 3


def test_defensive_none_safety():
    """Adversarial [I1]: Optional fields safely handled without AttributeError when None."""
    dp = TrafficDataPoint(
        tenant_id="tenant-null",
        timestamp=datetime.now(timezone.utc),
        request_count=1,
        metadata=None,
    )
    assert dp.metadata is None

    pred = ForecastPrediction(
        tenant_id="tenant-null",
        predicted_peak_time=datetime.now(timezone.utc),
        recommended_prewarm_time=datetime.now(timezone.utc),
        confidence=0.85,
        metadata=None,
    )
    assert pred.metadata is None

    forecaster = WorkloadForecaster()
    forecaster.record_event(dp)

    # Test handling with None arguments or empty datasets
    empty_preds = forecaster.predict_upcoming_peaks(
        current_time=datetime.now(timezone.utc),
        forecast_horizon_seconds=None,  # should default gracefully
    )
    assert isinstance(empty_preds, list)
