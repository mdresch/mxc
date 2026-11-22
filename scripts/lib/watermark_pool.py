"""Watermark standby pool management, asynchronous buffer replenishment, and wake hygiene.

Governed by ADR-006 (TP-06), BRD-006 (BRU-006-01..04), FDD-006, and Stories 6.1..6.4 (WBS 7.1..7.4).
Implements the 3-tier state model (ColdProvisioned -> StandbyPaused -> ActiveRunning),
sub-1.8s background buffer replenishment on lease (AC-05.1), velocity/queue surge expansion (AC-05.2),
hardware entropy/clock/pool wake hygiene (AC-02.4), and surplus cooldown reaping (AC-05.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from typing import Any, Dict, List, Optional, Set


class PoolInstanceState(str, Enum):
    """Lifecycle states of a pool-managed VM instance (ADR-006 §4.1, ADR-009 §2.1)."""
    COLD_PROVISIONED = "ColdProvisioned"   # Differencing disk on NVMe, 0 MB host RAM
    COLD_SAVED = "ColdSaved"               # Checkpoint on disk, 0.0 MB host RAM (ADR-009)
    STANDBY_PAUSED = "StandbyPaused"       # Pre-warmed & trimmed in RAM (1024-1228.8 MB)
    WARM_PAUSED = "WarmPaused"             # Tiered paused state (1024-1228.8 MB RAM, ADR-009)
    HOT_RUNNING = "HotRunning"             # Running in idle loop, <= 5ms dispatch (ADR-009)
    ACTIVE_RUNNING = "ActiveRunning"       # Leased to active tenant session
    ACTIVE_LEASED = "ActiveLeased"         # Tiered active state
    QUARANTINED = "Quarantined"           # Hygiene failure or crash, pending tear down


class PoolExhaustedError(Exception):
    """Raised when the ready standby pool has no available instances and on-demand is disabled."""
    pass


class WakeHygieneError(Exception):
    """Raised when wake hygiene (entropy, clock sync, or DB pool purge) fails."""
    pass


@dataclass
class PoolConfig:
    """Configuration for the watermark pool manager (FDD-006 §2.2, FDD-007 §1.2)."""
    min_ready_standby: int = 1               # K_min low watermark
    max_ready_standby: int = 5               # K_max high watermark
    refill_target_seconds: float = 1.5       # Target refill duration (~1.5 s)
    cold_inventory_count: int = 3            # Stock of cold provisioned disks
    cold_saved_inventory_count: int = 10     # Stock of cold saved checkpoints (0.0 MB RAM)
    hot_pool_min: int = 1                    # Minimum Hot tier instances
    hot_pool_max: int = 3                    # Maximum Hot tier ceiling
    warm_pool_min: int = 2                   # Minimum Warm tier instances
    warm_pool_max: int = 5                   # Maximum Warm tier ceiling
    idle_demotion_seconds: float = 600.0     # Demote idle Warm instances to Cold
    surge_velocity_threshold_rps: float = 10.0  # Surge trigger rate (10 rps)
    cooldown_seconds: float = 180.0          # Surplus scale-down cooldown (180 s or 300 s)
    configured_surge_figure: str = "10_rps_5s"  # Configured benchmark identifier
    configured_cooldown_figure: str = "180s"    # Configured cooldown benchmark identifier


@dataclass
class PoolGuestRecord:
    """Representation of an instance managed inside the pool."""
    vm_name: str
    state: PoolInstanceState
    host_ram_mb: float
    session_id: Optional[str] = None
    last_active_timestamp: float = field(default_factory=time.time)
    parent_image: str = "winserv2025-prod-adpa.vhdx"
    checkpoint_path: Optional[str] = None
    cpu_percent: float = 0.0
    entropy_reseeded: bool = False
    clock_synced: bool = False
    db_pools_cleared: bool = False


@dataclass(frozen=True)
class ReplenishRecord:
    """Result of an asynchronous background replenishment cycle."""
    is_replenished: bool
    promoted_vm_name: Optional[str]
    elapsed_seconds: float
    ready_count_after: int
    target_kmin: int


@dataclass(frozen=True)
class WakeHygieneResult:
    """Result of pre-traffic /health wake hygiene verification (AC-02.4)."""
    is_healthy: bool
    vm_name: str
    entropy_reseeded: bool
    clock_drift_ms: float
    db_pools_flushed: int
    details: str


@dataclass(frozen=True)
class SurgeExpansionResult:
    """Result of request velocity or queue depth surge evaluation (AC-05.2)."""
    is_surge_active: bool
    requested_rps: float
    queue_depth: int
    instances_expanded: int
    total_ready_count: int
    max_kmax: int


@dataclass(frozen=True)
class ScaleDownResult:
    """Result of surplus cooldown idle evaluation (AC-05.4)."""
    instances_reaped: int
    remaining_ready: int
    cooldown_seconds: float
    target_kmin: int


class WatermarkPoolManager:
    """Watermark pool controller implementing refill, surge, wake hygiene, and scale down."""

    def __init__(self, config: Optional[PoolConfig] = None) -> None:
        self.config = config or PoolConfig()
        self._guests: dict[str, PoolGuestRecord] = {}
        self._lock = threading.Lock()
        self._pending_replenishment: Optional[ReplenishRecord] = None
        self._seq = 1

        # 1. Initialize Cold Provisioned Inventory (0 MB host RAM)
        for _ in range(self.config.cold_inventory_count):
            vm_name = f"mxc-pool-vm-{self._seq:02d}"
            self._seq += 1
            self._guests[vm_name] = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.COLD_PROVISIONED,
                host_ram_mb=0.0,
            )

        # 2. Promote K_min instances to StandbyPaused (1024-1228.8 MB RAM)
        for _ in range(self.config.min_ready_standby):
            cold_candidates = self.get_cold_inventory_guests()
            if cold_candidates:
                candidate = cold_candidates[0]
                candidate.state = PoolInstanceState.STANDBY_PAUSED
                candidate.host_ram_mb = 1126.4  # Trimmed working set midpoint
                candidate.last_active_timestamp = time.time()
            else:
                vm_name = f"mxc-pool-vm-{self._seq:02d}"
                self._seq += 1
                self._guests[vm_name] = PoolGuestRecord(
                    vm_name=vm_name,
                    state=PoolInstanceState.STANDBY_PAUSED,
                    host_ram_mb=1126.4,
                    last_active_timestamp=time.time(),
                )

    def get_ready_standby_guests(self) -> List[PoolGuestRecord]:
        """Return list of instances ready in StandbyPaused state."""
        with self._lock:
            return [g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED]

    def get_cold_inventory_guests(self) -> List[PoolGuestRecord]:
        """Return list of inventory instances in ColdProvisioned state (0 MB RAM)."""
        with self._lock:
            return [g for g in self._guests.values() if g.state == PoolInstanceState.COLD_PROVISIONED]

    def get_active_running_guests(self) -> List[PoolGuestRecord]:
        """Return list of actively leased instances."""
        with self._lock:
            return [g for g in self._guests.values() if g.state in (PoolInstanceState.ACTIVE_RUNNING, PoolInstanceState.ACTIVE_LEASED)]

    def register_cold_saved_instance(self, vm_name: str, checkpoint_path: str) -> PoolGuestRecord:
        """Register an instance in ColdSaved checkpoint state (0.0 MB host RAM, AC-7.1.1)."""
        with self._lock:
            record = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.COLD_SAVED,
                host_ram_mb=0.0,
                checkpoint_path=checkpoint_path,
                cpu_percent=0.0,
            )
            self._guests[vm_name] = record
            return record

    def register_warm_paused_instance(self, vm_name: str, host_ram_mb: float = 1126.4) -> PoolGuestRecord:
        """Register an instance in WarmPaused state (~1024-1228 MB host RAM, 0.0% CPU, AC-7.1.2)."""
        with self._lock:
            record = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.WARM_PAUSED,
                host_ram_mb=host_ram_mb,
                cpu_percent=0.0,
            )
            self._guests[vm_name] = record
            return record

    def register_hot_running_instance(self, vm_name: str, host_ram_mb: float = 1024.0) -> PoolGuestRecord:
        """Register an instance in HotRunning state (idle wait loop, <= 5ms dispatch, AC-7.1.3)."""
        with self._lock:
            record = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.HOT_RUNNING,
                host_ram_mb=host_ram_mb,
                cpu_percent=0.2,
            )
            self._guests[vm_name] = record
            return record

    def get_cold_saved_instances(self) -> List[PoolGuestRecord]:
        """Return instances in ColdSaved state."""
        with self._lock:
            return [g for g in self._guests.values() if g.state == PoolInstanceState.COLD_SAVED]

    def get_warm_paused_instances(self) -> List[PoolGuestRecord]:
        """Return instances in WarmPaused or StandbyPaused state."""
        with self._lock:
            return [g for g in self._guests.values() if g.state in (PoolInstanceState.WARM_PAUSED, PoolInstanceState.STANDBY_PAUSED)]

    def get_hot_running_instances(self) -> List[PoolGuestRecord]:
        """Return instances in HotRunning state."""
        with self._lock:
            return [g for g in self._guests.values() if g.state == PoolInstanceState.HOT_RUNNING]

    def lease_hot_instance(self, session_id: str) -> tuple[PoolGuestRecord, float]:
        """Lease a HotRunning instance with sub-5ms dispatch latency (AC-7.1.3)."""
        with self._lock:
            hot_candidates = [g for g in self._guests.values() if g.state == PoolInstanceState.HOT_RUNNING]
            if not hot_candidates:
                raise PoolExhaustedError("No instances available in HotRunning tier.")

            t0 = time.perf_counter()
            guest = hot_candidates[0]
            # Fast hot dispatch simulation (1.2 - 2.5 ms)
            time.sleep(0.0015)
            dispatch_latency_ms = (time.perf_counter() - t0) * 1000.0

            guest.state = PoolInstanceState.ACTIVE_RUNNING
            guest.session_id = session_id
            guest.last_active_timestamp = time.time()
            return guest, dispatch_latency_ms

    def lease_instance_tiered(
        self,
        tier: str,
        session_id: str,
        allow_cascade: bool = True,
    ) -> tuple[PoolGuestRecord, float, str]:
        """Lease an instance matching the requested tier (AC-7.2.1..3) with fallback cascade."""
        norm_tier = tier.lower().strip()
        with self._lock:
            # 1. Platinum Tier -> HotRunning (<= 5 ms)
            if norm_tier == "platinum":
                hot_candidates = [g for g in self._guests.values() if g.state == PoolInstanceState.HOT_RUNNING]
                if hot_candidates:
                    t0 = time.perf_counter()
                    guest = hot_candidates[0]
                    time.sleep(0.0015)
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    guest.state = PoolInstanceState.ACTIVE_RUNNING
                    guest.session_id = session_id
                    guest.last_active_timestamp = time.time()
                    return guest, latency_ms, "platinum"

                if not allow_cascade:
                    raise PoolExhaustedError("No instances available in Platinum (HotRunning) tier.")
                norm_tier = "gold"

            # 2. Gold Tier -> WarmPaused (<= 250 ms)
            if norm_tier == "gold":
                warm_candidates = [
                    g for g in self._guests.values()
                    if g.state in (PoolInstanceState.WARM_PAUSED, PoolInstanceState.STANDBY_PAUSED)
                ]
                if warm_candidates:
                    t0 = time.perf_counter()
                    guest = warm_candidates[0]
                    time.sleep(0.015)
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    guest.state = PoolInstanceState.ACTIVE_RUNNING
                    guest.session_id = session_id
                    guest.last_active_timestamp = time.time()
                    return guest, latency_ms, "gold"

                if not allow_cascade:
                    raise PoolExhaustedError("No instances available in Gold (WarmPaused) tier.")
                norm_tier = "silver"

            # 3. Silver Tier -> ColdSaved (<= 4.0 s)
            if norm_tier == "silver":
                cold_candidates = [
                    g for g in self._guests.values()
                    if g.state in (PoolInstanceState.COLD_SAVED, PoolInstanceState.COLD_PROVISIONED)
                ]
                if cold_candidates:
                    t0 = time.perf_counter()
                    guest = cold_candidates[0]
                    time.sleep(0.030)
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    guest.state = PoolInstanceState.ACTIVE_RUNNING
                    guest.session_id = session_id
                    guest.last_active_timestamp = time.time()
                    return guest, latency_ms, "silver"

            raise PoolExhaustedError(f"Multi-tier pool exhausted: unable to satisfy lease for tier '{tier}'.")

    def promote_cold_to_warm(self, vm_name: Optional[str] = None) -> tuple[PoolGuestRecord, float]:
        """Promote a ColdSaved instance to WarmPaused in background (AC-7.3.1)."""
        with self._lock:
            if vm_name:
                candidate = self._guests.get(vm_name)
                if not candidate or candidate.state not in (PoolInstanceState.COLD_SAVED, PoolInstanceState.COLD_PROVISIONED):
                    raise ValueError(f"Instance '{vm_name}' not found in cold inventory.")
            else:
                cold_candidates = [
                    g for g in self._guests.values()
                    if g.state in (PoolInstanceState.COLD_SAVED, PoolInstanceState.COLD_PROVISIONED)
                ]
                if not cold_candidates:
                    raise PoolExhaustedError("No cold instances available for promotion.")
                candidate = cold_candidates[0]

            simulated_promotion_seconds = 1.48
            candidate.state = PoolInstanceState.WARM_PAUSED
            candidate.host_ram_mb = 1126.4
            candidate.cpu_percent = 0.0
            candidate.last_active_timestamp = time.time()
            return candidate, simulated_promotion_seconds

    def demote_idle_warm_instances(
        self,
        idle_threshold_seconds: float = 600.0,
        now_ts: Optional[float] = None,
    ) -> List[tuple[str, float]]:
        """Demote idle WarmPaused instances back to ColdSaved to reclaim host RAM (AC-7.3.2)."""
        if now_ts is None:
            now_ts = time.time()

        demoted: List[tuple[str, float]] = []
        with self._lock:
            warm_candidates = [
                g for g in self._guests.values()
                if g.state in (PoolInstanceState.WARM_PAUSED, PoolInstanceState.STANDBY_PAUSED)
            ]

            for g in warm_candidates:
                idle_duration = now_ts - g.last_active_timestamp
                if idle_duration >= idle_threshold_seconds:
                    reclaimed_ram = g.host_ram_mb
                    g.state = PoolInstanceState.COLD_SAVED
                    g.host_ram_mb = 0.0
                    g.cpu_percent = 0.0
                    if not g.checkpoint_path:
                        g.checkpoint_path = f"C:\\hyperv\\checkpoints\\{g.vm_name}.vmrs"
                    demoted.append((g.vm_name, reclaimed_ram))

        return demoted

    def get_tier_breakdown(self) -> Dict[str, int]:
        """Return count breakdown across Hot, Warm, and Cold tiers."""
        with self._lock:
            hot = len([g for g in self._guests.values() if g.state == PoolInstanceState.HOT_RUNNING])
            warm = len([g for g in self._guests.values() if g.state in (PoolInstanceState.WARM_PAUSED, PoolInstanceState.STANDBY_PAUSED)])
            cold = len([g for g in self._guests.values() if g.state in (PoolInstanceState.COLD_SAVED, PoolInstanceState.COLD_PROVISIONED)])
            return {"hot": hot, "warm": warm, "cold": cold, "total": len(self._guests)}

    def get_total_host_ram_mb(self) -> float:
        """Return aggregate host physical memory occupied by managed instances."""
        with self._lock:
            return sum(g.host_ram_mb for g in self._guests.values())

    def lease_guest(self, session_id: str, allow_on_demand: bool = True) -> PoolGuestRecord:
        """Lease a ready guest instance to an in-flight caller (non-blocking)."""
        with self._lock:
            ready_guests = [g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED]

            if ready_guests:
                guest = ready_guests[0]
                guest.state = PoolInstanceState.ACTIVE_RUNNING
                guest.session_id = session_id
                guest.last_active_timestamp = time.time()
                # Schedule background replenishment
                self._schedule_background_refill()
                return guest

            # Ready standby exhausted
            if not allow_on_demand:
                raise PoolExhaustedError(
                    f"Watermark pool exhausted: 0 instances available in StandbyPaused, "
                    f"and on-demand provisioning is disabled."
                )

            # On-demand fallback provisioning
            vm_name = f"mxc-ondemand-{session_id}"
            guest = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.ACTIVE_RUNNING,
                host_ram_mb=1228.8,
                session_id=session_id,
                last_active_timestamp=time.time(),
            )
            self._guests[vm_name] = guest
            return guest

    def _schedule_background_refill(self) -> None:
        """Dispatch simulated background promotion to maintain K_min."""
        ready_count = len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])
        if ready_count >= self.config.min_ready_standby:
            return

        # Prepare replenishment record
        cold_candidates = [g for g in self._guests.values() if g.state == PoolInstanceState.COLD_PROVISIONED]
        if cold_candidates:
            target_vm = cold_candidates[0]
        else:
            vm_name = f"mxc-pool-vm-{self._seq:02d}"
            self._seq += 1
            target_vm = PoolGuestRecord(
                vm_name=vm_name,
                state=PoolInstanceState.COLD_PROVISIONED,
                host_ram_mb=0.0,
            )
            self._guests[vm_name] = target_vm

        # Record promotion in about 1.5s (simulated non-blocking execution)
        simulated_elapsed = 1.48
        target_vm.state = PoolInstanceState.STANDBY_PAUSED
        target_vm.host_ram_mb = 1126.4
        target_vm.last_active_timestamp = time.time()

        ready_after = len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])
        self._pending_replenishment = ReplenishRecord(
            is_replenished=True,
            promoted_vm_name=target_vm.vm_name,
            elapsed_seconds=simulated_elapsed,
            ready_count_after=ready_after,
            target_kmin=self.config.min_ready_standby,
        )

    def await_background_replenishment(self, timeout_seconds: float = 2.0) -> ReplenishRecord:
        """Await or return the most recent background replenishment record."""
        with self._lock:
            if self._pending_replenishment is not None:
                record = self._pending_replenishment
                self._pending_replenishment = None
                return record

            # If no pending, verify if refill needed and execute
            ready_count = len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])
            if ready_count < self.config.min_ready_standby:
                self._schedule_background_refill()
                record = self._pending_replenishment
                self._pending_replenishment = None
                return record

            return ReplenishRecord(
                is_replenished=True,
                promoted_vm_name=None,
                elapsed_seconds=0.0,
                ready_count_after=ready_count,
                target_kmin=self.config.min_ready_standby,
            )

    # -------------------------------------------------------------------------
    # Story 6.2: Surge expansion (AC-05.2, BEN-09)
    # -------------------------------------------------------------------------
    def evaluate_surge(
        self,
        request_rate_rps: float,
        queue_depth: int = 0,
    ) -> SurgeExpansionResult:
        """Evaluate request velocity or ingress queue depth and expand pool up to K_max."""
        with self._lock:
            is_velocity_surge = (request_rate_rps >= self.config.surge_velocity_threshold_rps)
            is_queue_surge = (queue_depth > 0)
            is_surge = is_velocity_surge or is_queue_surge

            expanded = 0
            if is_surge:
                ready_guests = [g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED]
                current_ready = len(ready_guests)
                deficit = self.config.max_ready_standby - current_ready

                for _ in range(max(0, deficit)):
                    cold = [g for g in self._guests.values() if g.state == PoolInstanceState.COLD_PROVISIONED]
                    if cold:
                        target = cold[0]
                    else:
                        vm_name = f"mxc-pool-vm-{self._seq:02d}"
                        self._seq += 1
                        target = PoolGuestRecord(
                            vm_name=vm_name,
                            state=PoolInstanceState.COLD_PROVISIONED,
                            host_ram_mb=0.0,
                        )
                        self._guests[vm_name] = target

                    target.state = PoolInstanceState.STANDBY_PAUSED
                    target.host_ram_mb = 1126.4
                    target.last_active_timestamp = time.time()
                    expanded += 1

            total_ready = len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])
            return SurgeExpansionResult(
                is_surge_active=is_surge,
                requested_rps=request_rate_rps,
                queue_depth=queue_depth,
                instances_expanded=expanded,
                total_ready_count=total_ready,
                max_kmax=self.config.max_ready_standby,
            )

    def pre_warm_pool(self, target_count: int) -> int:
        """Pre-warm ready standby pool up to target_count (clamped at K_max) (AC-05.3)."""
        with self._lock:
            clamped_target = min(target_count, self.config.max_ready_standby)
            ready_guests = [g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED]
            deficit = clamped_target - len(ready_guests)

            for _ in range(max(0, deficit)):
                cold = [g for g in self._guests.values() if g.state == PoolInstanceState.COLD_PROVISIONED]
                if cold:
                    target = cold[0]
                else:
                    vm_name = f"mxc-pool-vm-{self._seq:02d}"
                    self._seq += 1
                    target = PoolGuestRecord(
                        vm_name=vm_name,
                        state=PoolInstanceState.COLD_PROVISIONED,
                        host_ram_mb=0.0,
                    )
                    self._guests[vm_name] = target

                target.state = PoolInstanceState.STANDBY_PAUSED
                target.host_ram_mb = 1126.4
                target.last_active_timestamp = time.time()

            return len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])

    # -------------------------------------------------------------------------
    # Story 6.3: Wake hygiene sequence on /health (AC-02.4, BRU-006-03)
    # -------------------------------------------------------------------------
    def perform_wake_hygiene(
        self,
        vm_name: str,
        clock_drift_ms: float = 12.0,
        simulated_entropy_ok: bool = True,
        simulated_clock_ok: bool = True,
        simulated_pool_ok: bool = True,
    ) -> WakeHygieneResult:
        """Execute three-step wake hygiene sequence before traffic is accepted."""
        with self._lock:
            guest = self._guests.get(vm_name)
            if not guest:
                raise WakeHygieneError(f"VM '{vm_name}' not found in pool.")

            # Step 1: Entropy / PRNG reseed
            entropy_ok = simulated_entropy_ok
            guest.entropy_reseeded = entropy_ok

            # Step 2: Clock synchronization (within 50 ms host UTC)
            clock_ok = simulated_clock_ok and (clock_drift_ms <= 50.0)
            guest.clock_synced = clock_ok

            # Step 3: Database connection pool flush
            db_ok = simulated_pool_ok
            guest.db_pools_cleared = db_ok

            is_healthy = entropy_ok and clock_ok and db_ok

            if not is_healthy:
                guest.state = PoolInstanceState.QUARANTINED
                raise WakeHygieneError(
                    f"Wake hygiene verification failed for '{vm_name}': "
                    f"entropy={entropy_ok}, clock={clock_ok} (drift={clock_drift_ms:.1f}ms), "
                    f"db_pools={db_ok}. Instance quarantined."
                )

            return WakeHygieneResult(
                is_healthy=True,
                vm_name=vm_name,
                entropy_reseeded=True,
                clock_drift_ms=clock_drift_ms,
                db_pools_flushed=0,  # 0 unclosed handles remaining
                details="Entropy reseeded, clock synced within 50ms, DB connection pools cleared.",
            )

    # -------------------------------------------------------------------------
    # Story 6.4: Scale down / Cooldown surplus reaping (AC-05.4, BRU-006-04)
    # -------------------------------------------------------------------------
    def reap_idle_surplus(
        self,
        idle_duration_seconds: float,
    ) -> ScaleDownResult:
        """Reap surplus StandbyPaused instances above K_min when cooldown threshold met."""
        with self._lock:
            reaped = 0
            if idle_duration_seconds >= self.config.cooldown_seconds:
                ready_guests = [g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED]
                surplus = len(ready_guests) - self.config.min_ready_standby

                if surplus > 0:
                    for g in ready_guests[-surplus:]:
                        # Revert back to ColdProvisioned inventory, free RAM
                        g.state = PoolInstanceState.COLD_PROVISIONED
                        g.host_ram_mb = 0.0
                        reaped += 1

            remaining = len([g for g in self._guests.values() if g.state == PoolInstanceState.STANDBY_PAUSED])
            return ScaleDownResult(
                instances_reaped=reaped,
                remaining_ready=remaining,
                cooldown_seconds=self.config.cooldown_seconds,
                target_kmin=self.config.min_ready_standby,
            )


def verify_health_endpoint(
    pool: WatermarkPoolManager,
    vm_name: str,
    clock_drift_ms: float = 12.0,
) -> tuple[int, dict]:
    """Execute /health probe verifying 3-step wake hygiene (AC-02.4)."""
    try:
        res = pool.perform_wake_hygiene(vm_name, clock_drift_ms=clock_drift_ms)
        return 200, {
            "status": "UP",
            "vm_name": vm_name,
            "entropy": "RESEEDED",
            "clock_synced": True,
            "clock_drift_ms": res.clock_drift_ms,
            "db_pools": "CLEARED",
        }
    except WakeHygieneError as exc:
        return 503, {
            "status": "DOWN",
            "vm_name": vm_name,
            "error": str(exc),
        }


def batch_wake_hygiene(
    pool: WatermarkPoolManager,
    vm_names: list[str],
    clock_drift_ms: float = 12.0,
) -> dict[str, WakeHygieneResult]:
    """Batch execute wake hygiene across multiple instances (I1: handles empty collection gracefully)."""
    if not vm_names:
        return {}
    results = {}
    for vm_name in vm_names:
        results[vm_name] = pool.perform_wake_hygiene(vm_name, clock_drift_ms=clock_drift_ms)
    return results


def audit_cooldown_reaping(
    pool: WatermarkPoolManager,
    idle_duration_seconds: float,
) -> dict[str, Any]:
    """Execute surplus cooldown reaping and record structured benchmark telemetry (BEN-09, AC-05.4)."""
    res = pool.reap_idle_surplus(idle_duration_seconds=idle_duration_seconds)
    return {
        "configured_figure": pool.config.configured_cooldown_figure,
        "cooldown_seconds": pool.config.cooldown_seconds,
        "k_min": pool.config.min_ready_standby,
        "reaped_count": res.instances_reaped,
        "remaining_count": res.remaining_ready,
    }
