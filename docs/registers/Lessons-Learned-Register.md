---
register: "lessons-learned-register"
governed_by: "ADR-010 (Lessons Learned Crystallization and Register)"
---

# Lessons Learned Register — <project name>

**Lifecycle role:** a light recap held once per epic, after its last user story is implemented and reviewed. It records how the code was created from the stories: traps, defects and review findings. It is not the formal lessons-learned review, and it adds no approval gate and no `LearningStore` record type.

**Maintenance rule:** append-only. Entries are accepted by a human. A recap with nothing new is recorded as a short sign-off entry whose Epic/Phase contains `no-new-lessons` and whose propagation target reads `Tier 1 register sign-off`.

**Propagation tiers.** Tier 1 is this register (always). Tier 2 is the in-repo component skill under `.claude/skills/<component>/SKILL.md`. Tier 3 is the universal rule in the template repository.

## Index

| ID | Title | Epic / Source | Tier Scope | Date |
|---|---|---|---|---|
| `LL-001` | Zero-Padded Epic File Matching & AC Parsing Fallback | Epic 01 / Story 1.1 | Tier 2 (`scripts/spec_gate.py`) | 2026-11-21 |
| `LL-002` | Local Store Dir Environment Isolation for Pytest Session | Epic 01 / Story 1.1 | Tier 2 (`tests/conftest.py`) | 2026-11-21 |
| `LL-003` | Ingress Gateway Buffer Holding and Timeout Decoupling | Epic 02 / Story 2.2 | Tier 2 (`ingress-gateway/SKILL.md`) | 2026-11-21 |

## Entries

### LL-001 — Zero-Padded Epic File Matching & AC Parsing Fallback
- **Epic / Story:** Epic 001 / Story 1.1 (commit `9e454974`)
- **Scope:** Specification gatekeeper script (`scripts/spec_gate.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `scripts/spec_gate.py`
- **The Trap / Problem:** `scripts/spec_gate.py` raised `FileNotFoundError` when invoked on Epic 1 (`spec_gate.py 1.1`) because `find_epic_file` globbed only `epic-1-*.md` and `epic-1.md`, failing to match standard 3-digit zero-padded names like `epic-001-type-1-hyperv-generation-2.md`. Additionally, `parse_story_spec` failed to extract criteria when lines lacked `**AC_1:**` bold tags.
- **The Root Cause:** Inflexible file globbing and regex assumptions in `find_epic_file()` and `parse_story_spec()`.
- **Actionable Invariant / Rule:** Support zero-padded globs (`epic-{n:03d}-*.md`, `epic-{n:02d}-*.md`, `epic-{n}-*.md`) and provide a fallback bullet-point extractor for criteria under `**Acceptance Criteria:**`.

### LL-002 — Local Store Dir Environment Isolation for Pytest Session
- **Epic / Story:** Epic 001 / Story 1.1 (commit `9e454974`)
- **Scope:** Governance test runner environment (`tests/conftest.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `tests/conftest.py` / `implement-story`
- **The Trap / Problem:** When `$env:AGENT_LEARNING_LOCAL_STORE_DIR` was set at the user OS level to an external inaccessible path, `conftest.py` failed during session setup with `WinError 5 Access is denied`, halting all pytest tests.
- **The Root Cause:** `conftest.py` captures `os.environ.get("AGENT_LEARNING_LOCAL_STORE_DIR")` at initial import before fixtures run.
- **Actionable Invariant / Rule:** Set `$env:AGENT_LEARNING_LOCAL_STORE_DIR = "data/agent-learning/store"` at process scope before invoking python/pytest runners.

### LL-003 — Ingress Gateway Buffer Holding and Timeout Decoupling
- **Epic / Story:** Epic 002 / Story 2.2 (commit `e9e6e1c1`)
- **Scope:** JIT scale-to-zero reverse proxy gateway (`scripts/lib/ingress_gateway.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/ingress-gateway/SKILL.md`
- **The Trap / Problem:** Direct reverse proxying to a dormant or paused guest socket drops incoming HTTP connections and emits HTTP 502/504 errors, causing webhooks and external callers to abort.
- **The Root Cause:** Off-the-shelf reverse proxies assume downstream socket availability and fail closed on connection reset before hypervisor unpause completes.
- **Actionable Invariant / Rule:** Buffer the incoming socket, asynchronously dispatch `pool-lease` / `resume`, probe guest health on port 8080, and if `wake_timeout_ms` expires, return HTTP 503 with a structured `Retry-After: 2` header, never exposing 502 or 504 to the caller.

### LL-004 — Pre-Checkpoint Connection Pool Sterilization & JIT Warm-Up Decoupling
- **Epic / Story:** Epic 003 / Story 3.2 (commit `af0b7bc3`)
- **Scope:** Production image bake pipeline & warm baseline checkpointing (`scripts/lib/production_image.py`, `scripts/hyperv/bake_production_adpa_image.ps1`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/production-image/SKILL.md`
- **The Trap / Problem:** Checkpointing a running VM immediately after warm-up smoke tests captures open TCP sockets and database pool handles in the saved guest RAM image. When instances wake from the checkpoint later, stale socket descriptors trigger immediate protocol reset exceptions (ECONNRESET/broken pipe) and connection pool corruption.
- **The Root Cause:** Synthetic smoke probes initialize database client drivers and connection pools. Unless connection pools are explicitly purged and closed before hypervisor memory checkpointing, stateful network connections persist into the immutable snapshot.
- **Actionable Invariant / Rule:** Enforce `BRU-003-03`: Execute HTTP smoke on `localhost:8080/health` to trigger JIT compilation, invoke `/admin/clear-pools` to flush all open database handles to zero, pre-trim memory working sets, and abort checkpoint capture if any unclosed DB handles remain. Checkpoint must be named strictly `baseline-hot-ready`.

### LL-005 — Pre-Suspend Working Set Trimming Sequence & vCPU Execution State
- **Epic / Story:** Epic 004 / Story 4.2 (commit `2a4c5f64`)
- **Scope:** Hyper-V standby pool memory optimization (`scripts/lib/paused_ram.py`, `scripts/hyperv/mxc-hyperv.ps1`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/paused-ram-standby/SKILL.md`
- **The Trap / Problem:** Attempting to trim a guest's working set or engage the Hyper-V dynamic memory balloon driver after calling `Suspend-VM` fails or hangs indefinitely.
- **The Root Cause:** Hyper-V `Suspend-VM` (Paused state) completely halts guest vCPU scheduling. The Windows in-guest memory manager (`EmptyWorkingSet`) and Hyper-V integration components require active vCPUs to page out unneeded working set pages.
- **Actionable Invariant / Rule:** Enforce `BRU-004-04` & FDD-004: All memory compaction, garbage collection, and working set trimming must execute *before* `Suspend-VM` while guest vCPUs are in `Running` state. Only after trimming brings memory into the ~1.0–1.2 GB target window may `Suspend-VM` be invoked. Attempting to trim while `Paused` must immediately raise `TrimExecutionError`.
- **Scope Boundary & Lifecycle Caveat:** Pre-suspend trimming applies to the **golden image bake pipeline** (capturing `baseline-hot-ready`) and **recycled standby pool fleets** (ADR-005 §4.2 differencing-disk discard). In a **pure disposable whole-guest model** (ADR-005 §4.3), in-session post-request trimming is redundant and bypassed because memory is reclaimed by immediate hypervisor instance teardown (`Remove-VM`). Replenished standby instances spawn pre-trimmed directly from the warm golden checkpoint.

### LL-006 — Session Sterility, Ephemeral Differencing Rollback & Parent Immutability
- **Epic / Story:** Epic 005 / Stories 5.1..5.3 (commits `94ac04d0`, `9c05c98e`, `572b2c97`)
- **Scope:** Transient differencing disk lifecycle, vSwitch port ACLs, and dual discard reproduction (`scripts/lib/session_sterility.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/session-sterility/SKILL.md`
- **The Trap / Problem:** Reusing a virtual machine or its underlying disk across micro-execution sessions risks data bleed between tenants, lingering scratch files, and covert channel persistence.
- **The Root Cause:** File writes in a guest touch the filesystem. If stateful virtual hard disks persist after connection release, or if the parent baseline image is mutated by the guest OS, subsequent callers inherit previous session artifacts.
- **Actionable Invariant / Rule:** Enforce `AC-02.1`, `AC-02.2`, `AC-02.3`, `BEN-07`, and `BEN-12`:
  1. All guest writes must be strictly isolated to an ephemeral child `.avhdx` anchored at `baseline-hot-ready`.
  2. Upon session release or after 300 s idle with `active_open_requests == 0`, the `.avhdx` is deleted.
  3. Parent `winserv2025-prod-adpa.vhdx` SHA-256 hash must be verified bit-for-bit before and after session execution.
  4. Outbound network traffic is default-deny public internet; only approved internal endpoints on whitelisted ports (DNS `:53`, Kerberos `:88`, SQL `:1433`, PostgreSQL `:5432`, Private Blob `:443`) are permitted. Inbound is restricted strictly to reverse proxy on `:8080`.
  5. Both Path A (whole guest destruction) and Path B (`.avhdx` discard only) guarantee that subsequent sessions reproduce from the approved production image (`winserv2025-prod-adpa.vhdx`), strictly rejecting developer or unapproved parent images.

### LL-007 — Watermark Pool Sizing, Non-Blocking Refill, and Wake Hygiene Triple-Gate
- **Epic / Story:** Epic 006 / Stories 6.1..6.4 (commits `0dfde56c`, `09aa7090`, `6d392717`, `61c79d45`)
- **Scope:** Standby watermark pool replenishment, surge expansion, wake hygiene verification, and surplus cooldown (`scripts/lib/watermark_pool.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/watermark-pool/SKILL.md`
- **The Trap / Problem:** Static standby pools either run dry during request bursts (causing cold boot delays $\approx 3.5\text{ s}$) or consume excessive host RAM during idle lulls. Furthermore, waking suspended guests without re-synchronizing entropy, clock, and connection pools causes cryptographic duplicate states, Kerberos authentication token failures, and database protocol errors.
- **The Root Cause:** Snapshots freeze ephemeral in-guest state. On resume, PRNG state is deterministic unless reseeded from hardware, the guest clock lags host UTC by the duration of sleep, and client TCP sockets point to dead server-side handles.
- **Actionable Invariant / Rule:** Enforce `AC-05.1`, `AC-05.2`, `AC-02.4`, `AC-05.4`, and `BEN-09`:
  1. Maintain a 3-tier instance state model: `ColdProvisioned` (0 MB RAM), `StandbyPaused` (1024–1228.8 MB RAM), and `ActiveRunning`.
  2. When a ready standby guest is leased, an asynchronous background worker replenishes the buffer by promoting the next cold instance in $\approx 1.5\text{ s}$ ($\le 1.8\text{ s}$) without blocking the leased caller (`AC-05.1`).
  3. Under request velocity bursts ($\ge 10\text{ rps}$ or $5\text{ rps}$) or queue depth $> 0$, expand ready instances up to $K_{\max}$ (default 5); strictly clamp at $K_{\max}$ ceiling.
  4. Before accepting traffic on resume from `baseline-hot-ready`, the first `/health` probe must enforce three discrete gates: hardware PRNG reseed, clock sync within $50\text{ ms}$ of host UTC, and 100% database connection pool handle purge; failure immediately quarantines the instance and returns HTTP 503 (`AC-02.4`).
  5. After traffic normalizes and idle exceeds configured cooldown ($180\text{ s}$ or $300\text{ s}$), reap surplus instances back to cold inventory, strictly preserving the $K_{\min}$ low watermark (`AC-05.4`).

### LL-008 — Multi-Tier Standby Partitioning, Hot Dispatch Bounds & Dynamic Idle Demotion
- **Epic / Story:** Epic 007 / Stories 7.1..7.3 (commits `eb5e2754`, `823d617e`, `0d14ccba`)
- **Scope:** Multi-tier standby pool architecture, dispatch routing, and promotion/demotion lifecycle (`scripts/lib/watermark_pool.py`)
- **Date:** 2026-11-22
- **Tier 2/3 Propagation Target:** `.claude/skills/watermark-pool/SKILL.md`
- **The Trap / Problem:** Treating all standby instances identically under a single paused RAM state causes severe host memory pressure as tenant counts scale beyond 40 guests, while still subjecting premium interactive callers to ~200ms unpause latency. Conversely, moving instances to disk checkpoints naively risks tenant starvation if cold restore is called on a live critical path.
- **The Root Cause:** Homogeneous standby pools fail to differentiate between tenant SLAs and request velocity profiles. A running VM guarantees sub-5ms response but costs ~1.0–1.2 GB host RAM; a saved disk checkpoint costs 0.0 MB host RAM but takes 2–4 seconds to restore.
- **Actionable Invariant / Rule:** Enforce `BRU-007-01`..`05`, `AC-7.1.1`..`3`, `AC-7.2.1`..`3`, `AC-7.3.1`..`2`, and `BEN-15`/`BEN-17`:
  1. Maintain a three-tier instance state hierarchy: `HotRunning` (running wait loop, $\le 5\text{ ms}$ dispatch), `WarmPaused` (RAM standby, $\le 250\text{ ms}$ unpause), and `ColdSaved` (disk checkpoint, 0.0 MB host RAM, $\le 4.0\text{ s}$ restore).
  2. Map incoming tenant SLA tiers to dispatch targets (Platinum $\rightarrow$ Hot, Gold $\rightarrow$ Warm, Silver/Batch $\rightarrow$ Cold) with automatic cascade fallback if higher tiers are temporarily exhausted.
  3. All promotion from `ColdSaved` to `WarmPaused` must execute asynchronously in the background (~1.5 s) without blocking concurrent in-flight requests (`AC-7.3.1`).
  4. Instances remaining idle in `WarmPaused` exceeding the demotion threshold ($\ge 600\text{ s}$) must automatically save checkpoint state to disk and reclaim host RAM down to 0.0 MB (`AC-7.3.2`).

### LL-009 — Early TLS SNI Pre-Wake Concurrency & Time-Series Workload Pre-Warming
- **Epic / Story:** Epic 008 / Stories 8.1 & 8.2 (commits `290ed4c7`, `ef390897`)
- **Scope:** Early TLS ClientHello SNI snooper (`scripts/lib/tls_snooper.py`) and Time-series workload forecasting engine (`scripts/lib/workload_forecaster.py`)
- **Date:** 2026-11-22
- **Tier 2/3 Propagation Target:** `.claude/skills/ingress-gateway/SKILL.md`, `.claude/skills/workload-forecasting/SKILL.md`
- **The Trap / Problem:** Reactive wake imposes $\approx 200\text{--}280\text{ ms}$ pause while micro-instances unpause on the live request path. Even if buffered safely by the reverse proxy without 502/504 errors, interactive enterprise callers perceive delays $> 100\text{ ms}$. Furthermore, naively triggering pre-warm without forecasting leads to idle standby instance sprawl and memory pressure.
- **The Root Cause:** Waiting for the full TLS session handshake and HTTP header completion before dispatching `Resume-VM` wastes 40–80 ms of network negotiation time that could run concurrently with Hyper-V unpause. At macro scale, recurring shift start times (e.g. 08:55 AM) are highly predictable and should be pre-warmed ahead of time.
- **Actionable Invariant / Rule:** Enforce `BRU-008-01`..`05`, `AC-8.1.1`..`2`, `AC-8.2.1`..`2`, `BEN-13`, `HYP-mxc-016`, `HYP-mxc-020`:
  1. Ingress gateway must parse TLS `ClientHello` frames and extract SNI within $\le 5\text{ ms}$ non-blocking, immediately dispatching async wake to pool manager before TLS session key exchange completes.
  2. Non-TLS or malformed traffic must pass through safely to standard HTTP handler without throwing exceptions.
  3. Workload forecaster models recurring shift start times and cron patterns, issuing pre-warm predictions $\ge 60\text{ s}$ in advance with $\ge 90\%$ accuracy.
  4. Pre-warming schedules promote instances into `WarmPaused` or `HotRunning` before client requests arrive, achieving 0 ms perceived wake latency.
  5. Optional parameters and fields must be defensively handled without `AttributeError` when None.
  6. Unused pre-warmed instances are bounded by the 180s cooldown timer (`AC-05.4`) and returned to cold inventory if unleased.

### LL-010 — Hyper-V Host Page Deduplication, COW Isolation & Fleet Density Floor
- **Epic / Story:** Epic 009 / Stories 9.1 & 9.2 (commits `b00b2f12`, `30bdb0c3`)
- **Scope:** Hyper-V memory combining configuration, diagnostic performance counters, effective host RAM floor, and COW isolation (`scripts/lib/memory_combining_probe.py`)
- **Date:** 2026-11-22
- **Tier 2/3 Propagation Target:** `.claude/skills/memory-deduplication/SKILL.md`
- **The Trap / Problem:** Scaling identical Windows Server 2025 standby micro-instances beyond 40 guests on a single 64 GB host exhausts host physical RAM if instances are treated as private allocations (640–1024 MB each). Furthermore, sharing physical memory across separate tenant VMs risks cross-tenant side-channel contamination or memory corruption if page isolation is not strictly hardware-enforced.
- **The Root Cause:** In a golden-bake Windows environment, large system regions (`ntoskrnl.exe`, .NET CLR, `user32.dll`, COM+ assemblies) are bit-for-bit identical across all guests.
- **Actionable Invariant / Rule:** Enforce `BRU-009-01`..`04`, `AC-9.1.1`..`2`, `AC-9.2.1`..`2`, `BEN-14`, `BEN-15`, `HYP-mxc-017`:
  1. Hypervisor memory combining scanner merges identical read-only 4 KB pages into shared physical host frames, compressing effective host RAM to $\le 450\text{ MB}$ per guest ($\le 18\text{ GB}$ total across 40 instances).
  2. Fleet deduplication ratio must achieve $\ge 40\%$ shared memory coverage across standby cohorts.
  3. Copy-On-Write (COW) memory isolation is strictly enforced: any guest write to a shared page triggers an immediate hardware page fault, cloning the page into private memory with 0 bytes leaked and 0 corruption of peer VMs.
  4. Background scanner CPU overhead must be clamped $\le 0.5\%$ aggregate host CPU during steady-state.
  5. Diagnostics monitor `\Hyper-V Dynamic Memory\Memory Combining Shared Pages`, `Saved Memory (MB)`, and `CPU Usage`.
