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
| `LL-014` | Host-Side Zero-Secret Boundary, Token-Boundary Env Scanning & MCP Firewall Precedence | Epic 013 / Stories 13.1..13.2 | Tier 2 (`.claude/skills/zero-secret-mcp-gateway/SKILL.md`) | 2026-11-25 |
| `LL-015` | Bounded Snapshot Fork Depth, Chunked VMBus Digests, UTF-8 BOM Normalization & IDE Worker Guard | Epic 014 / Stories 14.1..14.3 | Tier 2 (`.claude/skills/snapshot-fork-and-vmbus/SKILL.md`) | 2026-11-25 |
| `LL-016` | EU Evidence Ledger Retention/Tamper Invariants, Fail-Closed Enclave Precedence & Cache | Epic 015 / Stories 15.1..15.2 | Tier 2 (`.claude/skills/eu-evidence-and-enclave/SKILL.md`) | 2026-11-25 |
| `LL-017` | Reproducible ISO-to-Lean Auto-Registry Validation, Zero-Cloud Embed & Parent HIL Gate | Epic 016 / Stories 16.1..16.2 | Tier 2 (`.claude/skills/mxc-embed-appliance/SKILL.md`) | 2026-11-25 |
| `LL-018` | Ultra-Density Numeric Guards, Kernel TLS Pass-Through & Fail-Closed GPU-P Precedence | Epic 017 / Stories 17.1..17.3 | Tier 2 (`.claude/skills/frontier-density-and-gpu/SKILL.md`) | 2026-11-25 |

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

### LL-011 — Airgapped Cryptographic Supply Chain, Fail-Closed Precedence & Zero Hot-Path Verification
- **Epic / Story:** Epic 010 / Stories 10.1 & 10.2 (`spec-10_1-33cdce90`, `spec-10_2-0c4ffc6d`)
- **Scope:** Golden-image SLSA provenance envelope, CycloneDX 1.5 SBOM generator, and offline `PoolRegistrationGuard` (`scripts/lib/supply_chain_attestation.py`)
- **Date:** 2026-11-24
- **Tier 2/3 Propagation Target:** `.claude/skills/supply-chain-attestation/SKILL.md`
- **The Trap / Problem:** Relying on static SHA-256 registry entries alone leaves golden images vulnerable to local registry edits without cryptographic provenance, while online signature transparency lookups (e.g. live Rekor queries) break airgapped sovereign Hyper-V hosts and add unacceptable latency if placed on the VM dispatch path.
- **The Root Cause:** Conflating build-time/registration-time provenance verification with runtime dispatch, or assuming external internet connectivity on regulated hypervisor hosts.
- **Actionable Invariant / Rule:** Enforce `BRU-010-01`..`05` and `AC-10.1.1`..`10.2.3`:
  1. Serialize provenance payloads canonically (`sort_keys=True`, compact separators) and compare signatures/digests with constant-time `hmac.compare_digest`.
  2. Evaluate admission fail-closed in deterministic order: key revocation (`ERR_KEY_REVOKED`) $\rightarrow$ signature (`ERR_SIGNATURE_INVALID`) $\rightarrow$ expiry (`ERR_EXPIRED`) $\rightarrow$ VHDX digest (`ERR_DIGEST_MISMATCH`) $\rightarrow$ SBOM digest & forbidden packages (`ERR_SBOM_INVALID`).
  3. Execute 100% offline with zero network calls (verified with `socket.create_connection` monkeypatched to fail).
  4. Cache verified admissions in `PoolRegistrationGuard` so hot/warm dispatch checks remain O(1) in-memory (`0 ms` crypto overhead).

### LL-012 — Closed-Loop Host RAM Pressure Shedding, Hysteresis Override & Archetype Floor Guards
- **Epic / Story:** Epic 011 / Stories 11.1 & 11.2 (`spec-11_1-25e32156`, `spec-11_2-98b76e43`)
- **Scope:** Autonomous fleet economics scheduler, host pressure bands, anti-thrash hysteresis, and archetype sizing floor guard (`scripts/lib/fleet_economics.py`)
- **Date:** 2026-11-24
- **Tier 2/3 Propagation Target:** `.claude/skills/fleet-economics/SKILL.md`
- **The Trap / Problem:** Uniformly blocking all transitions during an anti-thrash dwell window delays emergency RAM shedding during sudden >85% host saturation, while allowing Hyper-V Dynamic Memory on Windows Desktop GUI guests causes silent `MemoryStatus: Low` VMConnect display stalls.
- **The Root Cause:** Treating emergency OOM protection and routine SLA rebalancing with the same hysteresis rule, and applying headless memory profiles to full GUI images.
- **Actionable Invariant / Rule:** Enforce `BRU-011-01`..`05` and `AC-11.1.1`..`11.2.2`:
  1. `CRITICAL` RAM pressure (`>85%`) MUST immediately override dwell hysteresis to shed idle `WarmPaused` guests to `ColdSaved` back to `<=80%`, while strictly preserving `target_hot >= platinum_k_min`.
  2. Non-critical transitions within `min_dwell_seconds` (`60s`) MUST hold to eliminate NVMe checkpoint thrashing.
  3. Enforce `desktop_gui >= 4096 MB` static RAM (`dynamic_memory_enabled=False`) and `>= 4` vCPUs, rejecting non-compliant specs with `ERR_ARCHETYPE_FLOOR_VIOLATION`.

### LL-013 — Auth-Before-Wake Invariance, Deny-by-Default Claims Routing & Mandatory TTL Reclamation (`ADR-008`)
- **Epic / Story:** Epic 012 / Stories 12.1 & 12.2 (`spec-12_1-0a227e26`, `spec-12_2-06896982`)
- **Scope:** Authentication-gated ingress, human OIDC/SAML & Entra Agent ID claims resolver, and TTL-bounded identity-bound VM leasing (`scripts/lib/auth_gated_leasing.py`)
- **Date:** 2026-11-24
- **Tier 2/3 Propagation Target:** `.claude/skills/auth-gated-leasing/SKILL.md`
- **The Trap / Problem:** Persisting identity-bound VM mappings without a hard TTL ceiling traps standby VMs indefinitely and breaks pool economics, while falling back to a default pool on unmapped claims opens a privilege-escalation vector to higher-trust golden images.
- **The Root Cause:** Leaving binding expiry unspecified (`ADR-008 §4.5`) and treating optional assertion/TTL parameters without defensive `None` guards.
- **Actionable Invariant / Rule:** Enforce `BRU-012-01`..`05` and `AC-12.1.1`..`12.2.3`:
  1. `route_mode="path_only"` keeps `ADR-002` path-routed leasing and `ADR-005` sterile rollback completely untouched.
  2. `route_mode="auth_gated"` MUST reject missing (`None`) or expired assertions before calling `pool_allocator` (`0` VMs woken).
  3. Claims mapping is strictly deny-by-default (`ERR_CLAIM_UNMAPPED`), supporting both `"human"` and `"entra_agent_id"` assertions.
  4. `binding_ttl_seconds` is strictly clamped to `[300, 86400]` (default `14400s`), and `sweep_expired_bindings()` returns expired `vm_id`s for mandatory `ADR-005` `.avhdx` sterile discard.

### LL-014 — Host-Side Zero-Secret Boundary, Token-Boundary Env Scanning & Protocol-Aware MCP Firewall Precedence (`ADR-014`)
- **Epic / Story:** Epic 013 / Stories 13.1 & 13.2 (`spec-13_1-a1cf178e`, `spec-13_2-0807f165`)
- **Scope:** Zero-secret host-side git bundle sync (`mxc-sync`), credential-injecting sidecar proxy, and MCP JSON-RPC protocol firewall (`scripts/lib/zero_secret_mcp_gateway.py`)
- **Date:** 2026-11-25
- **Tier 2/3 Propagation Target:** `.claude/skills/zero-secret-mcp-gateway/SKILL.md`
- **The Trap / Problem:** Naive substring scanning of guest environment variable names (e.g., matching `"PAT"` inside `"PATH"`) causes false-positive `ERR_STATIC_SECRET_DETECTED` failures on clean sandboxes, while unredacted failure audit logs or unpinned MCP server schemas expose host credentials or allow rug-pull tool mutations and recursive argument smuggling.
- **The Root Cause:** Conflating token-boundary credential key matching with raw substring checks, failing to scrub vault secrets across denied/error audit paths, and treating MCP `server_id`, `schema_sha256`, `tool_name`, and nested `arguments` checks as unordered or shallow rather than deterministic fail-closed protocol inspection.
- **Actionable Invariant / Rule:** Enforce `BRU-013-01`..`05` and `AC-13.1.1`..`13.2.3`:
  1. Scan `remote_url` and `guest_env` using token-boundary key matching (`PAT`, `TOKEN`, `SECRET`, `PASSWORD`, `SSH_AUTH_SOCK`, `PRIVATE_KEY`, `API_KEY`) plus credential material regexes (`https?://[^/\s@]+@`, `ghp_`, `github_pat_`, `glpat-`, `AKIA`, `BEGIN ... PRIVATE KEY`) so benign variables like `PATH` pass cleanly while static secrets fail closed (`ERR_STATIC_SECRET_DETECTED`) with `nic_count == 0`.
  2. Resolve host credentials in `CredentialSidecarProxy` (`<= 5 ms`) only for allowlisted `(target_host, secret_scope)` pairs with constant-time placeholder validation, never mutating input headers and scrubbing all vault secrets (`[REDACTED]`) from `audit_log` on both allowed and denied paths.
  3. Enforce `evaluate_mcp_call()` (`<= 2 ms`) in strict precedence: `ERR_MCP_SERVER_UNAPPROVED` -> `ERR_MCP_SCHEMA_DRIFT` (constant-time `hmac.compare_digest`) -> `ERR_MCP_TOOL_BLOCKED` -> `ERR_MCP_ARG_VIOLATION` (non-dict/`None` arguments or recursive key/value match on `blocked_arg_patterns`), with defensive `None`/empty safety and zero network calls.

### LL-015 — Bounded Snapshot Fork Depth, Chunked VMBus Digests, UTF-8 BOM Normalization & Zero-Secret IDE Worker Guard (`ADR-015`)
- **Epic / Story:** Epic 014 / Stories 14.1, 14.2 & 14.3 (`spec-14_1-f72b6317`, `spec-14_2-36f75f09`, `spec-14_3-34aecf5b`)
- **Scope:** Parallel `.avhdx` snapshot branching, chunked binary VMBus streaming, BOM-tolerant `wxc-exec` manifest parser, and ephemeral IDE worker profile validator (`scripts/lib/snapshot_fork_and_vmbus.py`)
- **Date:** 2026-11-25
- **Tier 2/3 Propagation Target:** `.claude/skills/snapshot-fork-and-vmbus/SKILL.md`
- **The Trap / Problem:** Unbounded `.avhdx` differencing chains degrade block lookup I/O; single-shot Base64 PowerShell/VMBus transfers hit the 8 KB `cmd.exe` ceiling; Windows PowerShell 5.1 `Set-Content -Encoding utf8` prepends `\xef\xbb\xbf` UTF-8 BOM bytes that break strict JSON parsers and reject legacy `"phase"` / `"sandboxId"` keys alongside CLI override flags; and unvalidated AI IDE worker profiles risk non-zero guest secrets or RAM starvation (`< 2048 MB`).
- **The Root Cause:** Missing depth/parallelism ceilings on snapshot branches, lack of sequenced per-chunk + stream digest framing, non-BOM-aware JSON parsing at the Windows CLI boundary, and permissive profile acceptance without zero-secret/floor guards.
- **Actionable Invariant / Rule:** Enforce `BRU-014-01`..`04` and `AC-14.1.1`..`14.3.2`:
  1. Bound snapshot forks to `max_parallel <= 5` (`ERR_FORK_BOUNDS_INVALID`) and `max_depth <= 4` (`ERR_FORK_DEPTH_EXCEEDED`), discarding losing branches with `0%` parent hash mutation and `None`/empty safety.
  2. Frame VMBus payloads into bounded chunks verifying sequential `seq`, `total_frames`, per-chunk SHA-256, and stream SHA-256 via `hmac.compare_digest` (`ERR_CHUNK_CHECKSUM_MISMATCH`), cleanly round-tripping `b""` <-> `[]`.
  3. Strip leading UTF-8 BOM bytes (`\xef\xbb\xbf`) before JSON parsing, preserve `"phase"` / `"sandboxId"` keys, and grant non-empty `cli_operation` / `cli_container_id` overrides deterministic precedence.
  4. Validate IDE worker profiles fail-closed (`ERR_WORKER_PROFILE_INVALID`) for `ide_client in {"cursor", "antigravity", "claude-code"}`, `zero_secret is True`, `sync_mode == "mxc-sync"`, non-empty `toolchain`/`toolchain_packages`, `guest_secrets_count == 0`, and finite `ram_mb >= 2048`.

### LL-016 — EU Evidence Ledger Retention/Tamper Invariants, Fail-Closed Enclave Precedence & Zero-Overhead Cache (`ADR-016`)
- **Epic / Story:** Epic 015 / Stories 15.1 & 15.2 (`spec-15_1-13a5d912`, `spec-15_2-8cf6474a`)
- **Scope:** Unified EU AI Act / DORA / NIS2 evidence ledger, Entra Conditional Access gate, Hit-L freeze-and-rollback circuit breaker, and vTPM 2.0 / AMD SEV-SNP / Intel TDX attestation (`scripts/lib/eu_evidence_and_enclave.py`)
- **Date:** 2026-11-25
- **Tier 2/3 Propagation Target:** `.claude/skills/eu-evidence-and-enclave/SKILL.md`
- **The Trap / Problem:** Evaluating PCR quote mismatch before checking `hardware_supported` masks unsupported confidential silicon as `ERR_PCR_ATTESTATION_FAILED` or risks faking compliance on standard hosts; meanwhile, Python `bool` subclassing of `int`, unguarded `None`/empty postures, and re-running attestation checks on dispatch violate the 180-day floor, raise `AttributeError`, or add dispatch latency.
- **The Root Cause:** Conflating missing hardware TEE support with quote mismatch, omitting explicit `bool`/`str`/`dict` type checks, and coupling admission-time verification with hot-path lookups.
- **Actionable Invariant / Rule:** Enforce `BRU-015-01`..`04` and `AC-15.1.1`..`15.2.3`:
  1. Reject `retention_days` on `None`, `bool`, non-`int`, or `< 180` (`ERR_RETENTION_BELOW_EU_FLOOR`); treat empty `verify_chain()` safely as `(True, "OK")`; verify `seq`, `prev_hash`, and canonical SHA-256 `entry_hash` via `hmac.compare_digest` (`ERR_LEDGER_CHAIN_BROKEN` on any single-field historical mutation).
  2. Guard `evaluate_entra_conditional_access()` against `None`/non-`dict`/`{}` without `AttributeError`, failing closed (`ERR_CONDITIONAL_ACCESS_DENIED`) unless `device_compliant is True`, `agent_blueprint_verified` is `True` when present, a non-empty `entra_agent_id` or `subject_id` exists, and `risk_level.lower()` is in `{"low", "none"}`.
  3. Execute `FreezeRollbackCircuitBreaker.freeze_and_rollback()` within `<= 250 ms` and append a verified `"FREEZE_AND_ROLLBACK"` event.
  4. Execute `verify_enclave_attestation()` 100% offline, checking `hardware_supported is True` first (`ERR_TEE_UNSUPPORTED`) before TEE profile/hex/PCR equality (`ERR_PCR_ATTESTATION_FAILED`), and cache verified admissions in `EnclaveAttestationCache` for O(1) `0.0 ms` hot-dispatch lookups.

### LL-017 — Reproducible ISO-to-Lean Auto-Registry Validation, Zero-Cloud Embed Precedence & Immutable Parent HIL Gate (`ADR-017`)
- **Epic / Story:** Epic 016 / Stories 16.1 & 16.2 (`spec-16_1-2b2d6d3d`, `spec-16_2-6327b6f2`)
- **Scope:** ISO-to-Lean CI registry entry builder, single-host "MXC Embed" preflight validator, and gated 5-Act HIL release verifier (`scripts/lib/mxc_embed_appliance.py`)
- **Date:** 2026-11-25
- **Tier 2/3 Propagation Target:** `.claude/skills/mxc-embed-appliance/SKILL.md`
- **The Trap / Problem:** Manual `golden_image_registry.json` hash edits drift from the built VHDX and break `ADR-012` SLSA attestation; meanwhile naive Python validation lets bare strings pass `Sequence` checks for `toolchain_packages`, lets `bool` values pass `isinstance(x, int)` checks, accepts `NaN`/`Inf` floats, or obscures network-egress and parent-hash-drift violations behind secondary error codes.
- **The Root Cause:** Missing strict type/shape guards (`bool` subclassing `int`, `str` implementing `Sequence`, trailing-newline `$` matching in regexes, non-finite IEEE-754 floats) and non-deterministic validation ordering across zero-cloud preflight and 5-Act HIL gates.
- **Actionable Invariant / Rule:** Enforce `BRU-016-01`..`03` and `AC-16.1.1`..`16.2.2`:
  1. `build_auto_registry_entry()` enforces non-blank `image_id`, non-empty non-string sequence `toolchain_packages` without blank items, strict 64-hex `iso_sha256`/`vhdx_sha256`, positive non-bool `int` `size_bytes`, `explorer_stripped=True`, and `compact_os_lzx=True`, emitting lowercase SHA-256 digests and `slsa_ready=True`.
  2. `run_mxc_embed_preflight()` executes 100% offline (`LL-011`) and fails closed in deterministic order: `ERR_NETWORK_EGRESS_ATTEMPTED` -> `ERR_PREFLIGHT_PREREQ_MISSING` -> `ERR_INSTALL_BUDGET_EXCEEDED` (rejecting `None`, `bool`, non-finite, `<= 0.0`, or `> 15.0` min).
  3. `evaluate_five_act_hil_gate()` checks constant-time `hmac.compare_digest` parent SHA-256 equality first (`ERR_PARENT_HASH_DRIFT`), then requires a 5-element `list` of `dict` acts all with `passed is True` (`ERR_HIL_ACT_FAILED`).

### LL-018 — Ultra-Density Numeric Guards, Kernel TLS Safe Pass-Through & Fail-Closed GPU-P Precedence (`ADR-018`)
- **Epic / Story:** Epic 017 / Stories 17.1..17.3 (`spec-17_1-4b2efa1e`, `spec-17_2-65c5c5ea`, `spec-17_3-3cb1f339`)
- **Scope:** Frontier density/NUMA planner, RAM-disk/DAX overlay allocator, kernel TLS/neural forecaster gate, subsystem differential telemetry matrix, and GPU-P sandbox admission (`scripts/lib/frontier_density_and_gpu.py`)
- **Date:** 2026-11-25
- **Tier 2/3 Propagation Target:** `.claude/skills/frontier-density-and-gpu/SKILL.md`
- **The Trap / Problem:** In Python, `bool` subclasses `int`, `NaN`/`inf` bypass simple `<=` range assertions, `None` or truncated non-TLS payloads can crash byte/dict inspectors with `AttributeError`/`IndexError`, `"COM+"` vs `"com_plus"` telemetry keys can drift across producers, and overlapping GPU-P failure conditions produce non-deterministic error codes without explicit precedence.
- **The Root Cause:** Treating numeric validation, packet parsing, telemetry key aliases, and hardware capability checks optimistically rather than enforcing strict finite-number type guards and deterministic fail-closed ordering.
- **Actionable Invariant / Rule:** Enforce `BRU-017-01`..`05` and `AC-17.1.1`..`17.3.2`:
  1. Reject `None`, `bool`, and non-finite (`NaN`/`inf`) numeric inputs consistently; enforce `<= 640.0 MB` paused floor (`ERR_PAUSED_FLOOR_EXCEEDED`), `>= 0.65` CrossGen2 ratio for `< 350.0 MB` effective RAM, `50.0 ms` disposable trim bypass, and `remote_numa_pages == 0` (`ERR_NUMA_REMOTE_PAGES`).
  2. Fail closed in `allocate_ramdisk_overlay()` (`ERR_RAMDISK_INVALID_REQUEST` -> `ERR_RAMDISK_QUOTA_EXCEEDED` -> `ERR_RAMDISK_MOUNT_LATENCY_EXCEEDED` over `50.0 ms`) without unhandled exceptions.
  3. Treat `None`, empty, or non-TLS payloads in `inspect_kernel_tls_promotion()` as safe pass-through (`is_tls_client_hello=False`, `sni_hint=None`) while enforcing finite `[0.0, 1.0]` forecaster bounds and promoting only at `confidence >= 0.90` and `false_positive_rate <= 0.05`.
  4. Normalize `"com+"` to `"com_plus"` case-insensitively and require all four subsystems (`wmi`, `com_plus`, `services`, `gpo`) to report `True` or `{"healthy": True}` (`ERR_SUBSYSTEM_DEGRADED` otherwise).
  5. Enforce deterministic GPU-P admission precedence (`ERR_GPUP_UNSUPPORTED` -> `ERR_GPUP_PARTITION_INVALID` -> `ERR_GPUP_SLA_BELOW_FLOOR` `< 0.85`) and avoid `math.isclose` (`IMP-024`).
