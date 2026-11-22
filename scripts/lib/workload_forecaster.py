"""Time-Series Workload Forecasting Engine (WBS 9.2).

Governing Artifacts:
- ADR-010: Predictive Wake Interception & Activity-Based Time-Series Forecasting
- BRD-008: Predictive Wake Interception & Activity Forecasting (BRU-008-03, BRU-008-04)
- FDD-008: Functional Design (§1.3 Time-Series Activity Forecaster)
- Epic 008: Story 8.2 (WBS 9.2)

Key Capabilities:
- Detect daily recurring shifts (e.g. 08:55 AM shift starts).
- Detect periodic recurring cron jobs (e.g. hourly or minutely intervals).
- Issue advance pre-warm predictions >= 60 seconds before traffic bursts.
- Orchestrate WatermarkPoolManager instances to WarmPaused or HotRunning.
- Defensive None-safety for all optional fields.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import statistics

from scripts.lib.watermark_pool import (
    PoolInstanceState,
    WatermarkPoolManager,
)


@dataclass
class TrafficDataPoint:
    """Historical traffic observation for a tenant."""
    tenant_id: str
    timestamp: datetime
    request_count: int = 1
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


@dataclass
class ForecastPrediction:
    """Predicted future workload burst with recommended pre-warming time."""
    tenant_id: str
    predicted_peak_time: datetime
    recommended_prewarm_time: datetime
    confidence: float = 0.90
    target_tier: str = "WarmPaused"
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.predicted_peak_time.tzinfo is None:
            self.predicted_peak_time = self.predicted_peak_time.replace(tzinfo=timezone.utc)
        if self.recommended_prewarm_time.tzinfo is None:
            self.recommended_prewarm_time = self.recommended_prewarm_time.replace(tzinfo=timezone.utc)


@dataclass
class PrewarmResult:
    """Result of triggering a pre-warming action."""
    tenant_id: str
    instance_id: Optional[str]
    achieved_tier: PoolInstanceState
    timestamp: datetime


class WorkloadForecaster:
    """Time-series forecaster that predicts tenant traffic patterns and triggers pre-warming."""

    def __init__(self, lead_time_seconds: float = 60.0):
        self.lead_time_seconds = float(lead_time_seconds) if lead_time_seconds is not None else 60.0
        self._history: Dict[str, List[TrafficDataPoint]] = {}

    def record_event(self, event: TrafficDataPoint) -> None:
        """Record a single tenant traffic data point."""
        if event is None or getattr(event, "tenant_id", None) is None:
            return
        tenant_id = event.tenant_id
        if tenant_id not in self._history:
            self._history[tenant_id] = []
        self._history[tenant_id].append(event)
        self._history[tenant_id].sort(key=lambda dp: dp.timestamp)

    def load_history(self, events: List[TrafficDataPoint]) -> None:
        """Load multiple history events."""
        if not events:
            return
        for e in events:
            self.record_event(e)

    def predict_upcoming_peaks(
        self,
        current_time: datetime,
        forecast_horizon_seconds: Optional[float] = 3600.0,
        lead_time_seconds: Optional[float] = None,
        confidence_threshold: Optional[float] = 0.85,
    ) -> List[ForecastPrediction]:
        """Predict upcoming traffic peaks for all recorded tenants within the horizon."""
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        horizon = float(forecast_horizon_seconds) if forecast_horizon_seconds is not None else 3600.0
        lead_time = float(lead_time_seconds) if lead_time_seconds is not None else self.lead_time_seconds
        conf_min = float(confidence_threshold) if confidence_threshold is not None else 0.85

        window_end = current_time + timedelta(seconds=horizon)
        predictions: List[ForecastPrediction] = []

        for tenant_id, points in self._history.items():
            if not points:
                continue

            # 1. Check for recurring time-of-day pattern (e.g. daily shifts)
            shift_prediction = self._detect_daily_pattern(
                tenant_id=tenant_id,
                points=points,
                current_time=current_time,
                window_end=window_end,
                lead_time=lead_time,
                conf_min=conf_min,
            )
            if shift_prediction is not None:
                predictions.append(shift_prediction)

            # 2. Check for periodic cron pattern (constant intervals e.g. hourly)
            cron_prediction = self._detect_cron_pattern(
                tenant_id=tenant_id,
                points=points,
                current_time=current_time,
                window_end=window_end,
                lead_time=lead_time,
                conf_min=conf_min,
            )
            if cron_prediction is not None:
                # Avoid duplicate if same predicted time
                if not any(
                    p.tenant_id == tenant_id
                    and abs((p.predicted_peak_time - cron_prediction.predicted_peak_time).total_seconds()) < 60
                    for p in predictions
                ):
                    predictions.append(cron_prediction)

        return predictions

    def _detect_daily_pattern(
        self,
        tenant_id: str,
        points: List[TrafficDataPoint],
        current_time: datetime,
        window_end: datetime,
        lead_time: float,
        conf_min: float,
    ) -> Optional[ForecastPrediction]:
        """Detect daily recurring patterns."""
        if len(points) < 3:
            return None

        # Extract seconds from midnight for each point
        seconds_of_day = [
            pt.timestamp.hour * 3600 + pt.timestamp.minute * 60 + pt.timestamp.second
            for pt in points
        ]
        mean_sec = statistics.mean(seconds_of_day)
        stdev_sec = statistics.stdev(seconds_of_day) if len(seconds_of_day) > 1 else 0.0

        if stdev_sec > 300.0:  # variance greater than 5 minutes -> not a consistent daily pattern
            return None

        # Candidate peak on the current day or next day
        cand_time = current_time.replace(
            hour=int(mean_sec // 3600),
            minute=int((mean_sec % 3600) // 60),
            second=int(mean_sec % 60),
            microsecond=0,
        )
        if cand_time < current_time:
            cand_time += timedelta(days=1)

        if current_time <= cand_time <= window_end:
            confidence = min(0.99, max(0.90, 1.0 - (stdev_sec / 300.0) * 0.1))
            if confidence >= conf_min:
                prewarm_time = cand_time - timedelta(seconds=lead_time)
                return ForecastPrediction(
                    tenant_id=tenant_id,
                    predicted_peak_time=cand_time,
                    recommended_prewarm_time=prewarm_time,
                    confidence=confidence,
                    target_tier="WarmPaused",
                    metadata={"pattern": "daily_recurring_shift", "stdev_seconds": stdev_sec},
                )
        return None

    def _detect_cron_pattern(
        self,
        tenant_id: str,
        points: List[TrafficDataPoint],
        current_time: datetime,
        window_end: datetime,
        lead_time: float,
        conf_min: float,
    ) -> Optional[ForecastPrediction]:
        """Detect fixed-interval cron patterns."""
        if len(points) < 3:
            return None

        # Compute adjacent inter-arrival intervals
        intervals = [
            (points[i + 1].timestamp - points[i].timestamp).total_seconds()
            for i in range(len(points) - 1)
        ]
        mean_interval = statistics.mean(intervals)
        stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0.0

        if mean_interval < 30.0 or (mean_interval > 0 and (stdev_interval / mean_interval) > 0.10):
            return None

        # Project next intervals from the last point
        last_time = points[-1].timestamp
        next_cand = last_time + timedelta(seconds=mean_interval)
        while next_cand < current_time:
            next_cand += timedelta(seconds=mean_interval)

        if current_time <= next_cand <= window_end:
            confidence = min(0.99, max(0.90, 1.0 - (stdev_interval / mean_interval)))
            if confidence >= conf_min:
                prewarm_time = next_cand - timedelta(seconds=lead_time)
                return ForecastPrediction(
                    tenant_id=tenant_id,
                    predicted_peak_time=next_cand,
                    recommended_prewarm_time=prewarm_time,
                    confidence=confidence,
                    target_tier="WarmPaused",
                    metadata={"pattern": "fixed_cron_interval", "interval_seconds": mean_interval},
                )
        return None

    def evaluate_accuracy(
        self,
        predictions: List[ForecastPrediction],
        actual_events: List[TrafficDataPoint],
        tolerance_seconds: float = 120.0,
    ) -> float:
        """Evaluate accuracy of predictions against actual traffic events (0.0 to 1.0)."""
        if not actual_events:
            return 1.0 if not predictions else 0.0
        if not predictions:
            return 0.0

        hits = 0
        for actual in actual_events:
            # Check if there exists a prediction for this tenant within tolerance
            match = any(
                p.tenant_id == actual.tenant_id
                and abs((p.predicted_peak_time - actual.timestamp).total_seconds()) <= tolerance_seconds
                for p in predictions
            )
            if match:
                hits += 1

        return hits / len(actual_events)

    def trigger_prewarm_schedule(
        self,
        pool_manager: WatermarkPoolManager,
        predictions: Optional[List[ForecastPrediction]] = None,
        current_time: Optional[datetime] = None,
        forecast_horizon_seconds: float = 300.0,
        lead_time_seconds: Optional[float] = None,
    ) -> List[PrewarmResult]:
        """Trigger pre-warming in WatermarkPoolManager for predictions due in the pre-warm window."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        if predictions is None:
            predictions = self.predict_upcoming_peaks(
                current_time=current_time,
                forecast_horizon_seconds=forecast_horizon_seconds,
                lead_time_seconds=lead_time_seconds,
            )

        results: List[PrewarmResult] = []

        for pred in predictions:
            # Check if current_time has reached the recommended prewarm window and is before peak
            if pred.recommended_prewarm_time <= current_time <= pred.predicted_peak_time:
                # Target instance needs to reach WarmPaused or HotRunning
                promoted_inst_name = None
                target_tier = PoolInstanceState.WARM_PAUSED

                try:
                    promoted_guest, _ = pool_manager.promote_cold_to_warm()
                    promoted_inst_name = promoted_guest.vm_name
                except Exception:
                    # Check if already warm instances exist
                    warm_guests = pool_manager.get_warm_paused_instances()
                    if warm_guests:
                        promoted_inst_name = warm_guests[0].vm_name

                if pred.target_tier.lower() == "hotrunning":
                    target_tier = PoolInstanceState.HOT_RUNNING
                    if promoted_inst_name:
                        pool_manager.register_hot_running_instance(promoted_inst_name)

                results.append(
                    PrewarmResult(
                        tenant_id=pred.tenant_id,
                        instance_id=promoted_inst_name,
                        achieved_tier=target_tier,
                        timestamp=current_time,
                    )
                )

        return results
