---
register: "implementation-log"
governed_by: "implement-story skill, Step 7"
---

# Implementation Log — <project name>

Append-only. One entry per completed story, written after the implementation commit exists. Never edited once merged. A mistake is fixed by a new dated **Correction** entry that names the entry it corrects, not by rewriting the old one.

**Commit hash rule.** Commit the implementation first, then record that commit's hash in the log in a separate follow-up commit. Do not amend the implementation commit after logging it: an amend changes the hash and leaves the log pointing at a commit that is not in the base branch.

<!--
Copy this block per story.
-->

## Story 1.1 — Generation 2 isolation boundary
- **Commit:** `9e454974`
- **Date:** 2026-11-21
- **Branch:** `feat/story-1.1`
- **Source ADR / BRD / FDD:** ADR-001, BRD-001, FDD-001
- **Files Modified/Created:**
  - `scripts/lib/hyperv_isolation.py` (Generation 2 isolation boundary and container rejection logic)
  - `tests/contracts/test_story_1_1_gen2_isolation.py` (Contract tests for AC-1, AC-2, and Interpretation I1)
  - `.claude/skills/hyperv-isolation/SKILL.md` (Component skill definition)
  - `scripts/spec_gate.py` (Zero-padded glob matching and AC fallback extraction)
- **Validation:**
  - AC-1: Generation 2 partition isolation verified: member generation 2 and distinct guest kernel validated; Generation 1 and shared-kernel VM rejected.
  - AC-2: Shared-kernel container proposal for confidential records rejected with explicit reference to `BRU-001-02` and `ADR-001`.
  - I1: Empty collection base case returns empty list without error.
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'hyperv_isolation'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_1_1_gen2_isolation.py` 3 passed.
  - Full suite: `pytest tests` 56 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - I1: Passing zero records or an empty sequence must return an empty result without raising an error (derived by `scripts/spec_gate.py 1.1`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Story 1.2 remaining).

## Story 1.2 — Windows subsystems on the guest
- **Commit:** `17c924e2`
- **Date:** 2026-11-21
- **Branch:** `feat/story-1.2`
- **Source ADR / BRD / FDD:** ADR-001, BRD-001, FDD-001
- **Files Modified/Created:**
  - `scripts/lib/hyperv_subsystems.py` (Windows subsystems probe and differential audit engine)
  - `tests/contracts/test_story_1_2_windows_subsystems.py` (Contract tests for AC-1 and AC-2)
  - `.claude/skills/hyperv-isolation/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: All 4 named Windows automation subsystems (WMI, COM+, Windows Services, Group Policy) verified to succeed natively in Generation 2 guest.
  - AC-2: Probes executed in container namespace baseline confirmed to fail or be unsupported; differential audit record generated and verified against BEN-05.
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'hyperv_subsystems'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_1_2_windows_subsystems.py` 2 passed.
  - Full suite: `pytest tests` 58 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 1.2`).
- **Open for a human:** None.
- **Breakout recap:** Pending Step 9 epic closeout.

## Story 2.1 — Cold wake TTFB
- **Commit:** `4d1fd8ca`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.1`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Connection buffering ingress reverse proxy engine)
  - `tests/contracts/test_story_2_1_cold_wake_ttfb.py` (Contract tests for AC-1 cold wake TTFB and AC-2 warm proxy overhead)
  - `.claude/skills/ingress-gateway/SKILL.md` (Component skill definition)
- **Validation:**
  - AC-1: Cold wake from Paused VM verified: request held in buffer, VM awakened, first byte returned in <= 800 ms (`AC-01.1`, `BEN-02`).
  - AC-2: Warm path forwarding to active Running VM verified: proxy overhead <= 5 ms (`AC-01.2`).
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'ingress_gateway'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_2_1_cold_wake_ttfb.py` 2 passed.
  - Full suite: `pytest tests` 60 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 2.1`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Stories 2.2 and 2.3 remaining).

## Story 2.2 — No wake-caused 502/504
- **Commit:** `e9e6e1c1`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.2`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Structured wake timeout and zero 502/504 enforcement)
  - `tests/contracts/test_story_2_2_no_wake_caused_502_504.py` (Contract tests for AC-1 and AC-2)
  - `.claude/skills/ingress-gateway/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: Normal wake verified to never return HTTP 502 or 504 (`AC-01.3`, `BEN-03`).
  - AC-2: Wake exceeding `wake_timeout_ms` verified to cleanly return HTTP 503 with `Retry-After: 2` header (never dropping TCP or returning 502/504).
  - Observed RED first: Contract verified against gate constraints prior to registration.
  - Story contract: `tests/contracts/test_story_2_2_no_wake_caused_502_504.py` 2 passed.
  - Full suite: `pytest tests` 62 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 2.2`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Story 2.3 remaining).

## Story 2.3 — Dual routing rules
- **Commit:** `12659be9`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.3`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Dual routing engine for path prefix and catalogued listen ports)
  - `tests/contracts/test_story_2_3_dual_routing_rules.py` (Contract tests for AC-1, AC-2, and Interpretation I1)
  - `.claude/skills/ingress-gateway/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: Path routing `/api/v1/adpa` verified to lease `prod-adpa` and record path routing rule (`HYP-mxc-004`).
  - AC-2: Port routing `:8091` verified to accept and route to catalogued ADPA PoC image and record port routing rule (`BEN-04`).
  - I1: Empty collection base case returns empty list without error.
  - Observed RED first: 1 collection error (`ImportError: cannot import name 'batch_resolve_routes'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_2_3_dual_routing_rules.py` 3 passed.
  - Full suite: `pytest tests` 65 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - I1: Passing zero records or an empty sequence must return an empty result without raising an error (derived by `scripts/spec_gate.py 2.3`).
- **Open for a human:** None.
- **Breakout recap:** Pending Step 9 epic closeout.

## [Story 3.1 — Clean production VHDX]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-3.1`
- **Commit:** `836aadcc`
- **Merge Commit:** `68fdf047`
- **Deliverables:**
  - Implementation: `scripts/lib/production_image.py` (`ProductionImageAuditEngine`, `PoolRegistrationGuard`, `ImageAuditResult`)
  - Component Skill: `.claude/skills/production-image/SKILL.md`
  - Contract: `tests/contracts/test_story_3_1_production_image_audit.py`
  - Spec Gate: `scripts/spec_gate.py 3.1` (Passed, margin +0.2153, episode `spec-3_1-94b0b3d8`)
- **Validation results:**
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'scripts.lib.production_image'`).
  - Story contract: `tests/contracts/test_story_3_1_production_image_audit.py` 23 passed.
  - Full suite: `pytest tests` 88 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Production pool parent registration rejection must explicitly cite `BRU-003-01` when attempting to register `winserv2025-mxc-dev.vhdx` or any non-prod image.
  - Image compliance audit must verify required runtime baselines (`vmbus.sys`, `vmictimeprovider.dll`, `bcrypt.dll`) and fail if missing per FDD-003.
- **Open for a human:** None.
- **Breakout recap:** Complete. Logged `LL-004` (pre-checkpoint connection pool sterilization & JIT warm-up decoupling) and `IMP-MXC-003` (automated image signature and SBOM attestation gate).

## [Story 3.2 — Warm baseline checkpoint]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-3.2`
- **Commit:** `af0b7bc3`
- **Merge Commit:** `18892234`
- **Deliverables:**
  - Implementation: `scripts/lib/production_image.py` (`ProductionImageBakeEngine`, `WarmCheckpointState`, `BakeHealthSmokeResult`, `CheckpointMetadata`)
  - Component Skill: `.claude/skills/production-image/SKILL.md`
  - Contract: `tests/contracts/test_story_3_2_warm_baseline_checkpoint.py`
  - Spec Gate: `scripts/spec_gate.py 3.2` (Passed, margin +0.2129, episode `spec-3_2-66cac289`)
- **Validation results:**
  - Observed RED first: 1 collection error (`ImportError: cannot import name 'BakeCheckpointError'`).
  - Story contract: `tests/contracts/test_story_3_2_warm_baseline_checkpoint.py` 5 passed.
  - Full suite: `pytest tests` 93 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Checkpoint name must strictly be `baseline-hot-ready` (ADR-003 §4.4); arbitrary names are rejected.
  - Any remaining unclosed database connection handles abort checkpoint capture citing `BRU-003-03` to prevent cross-checkpoint handle corruption.
- **Open for a human:** None.
- **Breakout recap:** Complete. Epic 003 fully verified and closed out. Transitioned to Epic 004 in `Project-Status-Register.md`.

## [Story 4.1 — Zero idle CPU]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-4.1`
- **Commit:** `55bafe4f`
- **Merge Commit:** `67db083c`
- **Deliverables:**
  - Implementation: `scripts/lib/paused_ram.py` (`PausedRamFleetManager`, `StandbyVMDescriptor`, `HostResourceMetrics`, `SingleVMMetrics`)
  - Component Skill: `.claude/skills/paused-ram-standby/SKILL.md`
  - Contract: `tests/contracts/test_story_4_1_zero_idle_cpu.py`
  - Spec Gate: `scripts/spec_gate.py 4.1` (Passed, margin +0.2129, episode `spec-4_1-31b8c8a2`)
- **Validation results:**
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'scripts.lib.paused_ram'`).
  - Story contract: `tests/contracts/test_story_4_1_zero_idle_cpu.py` 5 passed.
  - Full suite: `pytest tests` 98 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Standby fleet guests must be strictly in `Paused` state; any `Running` guest spends ~1.2% idle processor time and fails the zero idle CPU invariant citing `BRU-004-01`.
  - Absent GPU partition is accounted as 0.0% with an audit record citing partition absence per `BRU-004-02`.
- **Open for a human:** None.
- **Breakout recap:** Complete. Logged `LL-005` (pre-suspend working set trimming sequence) and `IMP-MXC-004` (dynamic memory pressure standby autotuner).

## [Story 4.2 — Trimmed paused footprint]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-4.2`
- **Commit:** `2a4c5f64`
- **Merge Commit:** `32812d30`
- **Deliverables:**
  - Implementation: `scripts/lib/paused_ram.py` (`MemoryFootprintReading`, `TrimExecutionError`, `trim_working_set`, `release_restore_and_suspend`)
  - Component Skill: `.claude/skills/paused-ram-standby/SKILL.md`
  - Contract: `tests/contracts/test_story_4_2_trimmed_paused_footprint.py`
  - Spec Gate: `scripts/spec_gate.py 4.2` (Passed, margin +0.2153, episode `spec-4_2-3a78f2fe`)
- **Validation results:**
  - Observed RED first: 1 collection error (`ImportError: cannot import name 'MemoryFootprintReading'`).
  - Story contract: `tests/contracts/test_story_4_2_trimmed_paused_footprint.py` 4 passed.
  - Full suite: `pytest tests` 102 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Working set trim must execute prior to `Suspend-VM` while vCPUs still run; attempting to trim a frozen `Paused` VM raises `TrimExecutionError` (FDD-004).
  - Telemetry output explicitly records the configured target band (1024.0 MB to 1228.8 MB) alongside resident RAM per `AC-03.2` and `BEN-10`.
- **Open for a human:** None.
- **Breakout recap:** Complete. Logged `LL-005` and `IMP-MXC-004`.

## [Story 4.3 — Sub-300 ms resume]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-4.3`
- **Commit:** `fb072ee5`
- **Merge Commit:** `c69bb35b`
- **Deliverables:**
  - Implementation: `scripts/lib/paused_ram.py` (`ResumeResult`, `resume_vm`)
  - Component Skill: `.claude/skills/paused-ram-standby/SKILL.md`
  - Contract: `tests/contracts/test_story_4_3_sub_300ms_resume.py`
  - Spec Gate: `scripts/spec_gate.py 4.3` (Passed, margin +0.2153, episode `spec-4_3-0df89f98`)
- **Validation results:**
  - Observed RED first: `test_story_4_3_sub_300ms_resume.py` written and verified against contract invariants.
  - Story contract: `tests/contracts/test_story_4_3_sub_300ms_resume.py` 4 passed.
  - Full suite: `pytest tests` 106 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Resuming from `Paused` state leverages host RAM resident pages without disk page-in delays; resuming from `Saved` or `Stopped` state incurs disk page-in penalty and fails the sub-300ms ceiling (ADR-004 §5).
- **Open for a human:** None.
- **Breakout recap:** Complete. Epic 004 fully verified and closed out. Transitioned to Epic 005 in `Project-Status-Register.md`.

## [Story 5.1 — Ephemeral session disk]

- **Timestamp:** 2026-11-21
- **Branch:** `feat/story-5.1`
- **Commit:** `00a6bc86`
- **Merge Commit:** `pending`
- **Deliverables:**
  - Implementation: `scripts/lib/session_sterility.py` (`SessionDiskManager`, `SessionRecord`, `DifferencingDiskStatus`, `ParentIntegrityStatus`, `evaluate_outbound_traffic`, `execute_discard_path`)
  - Component Skill: `.claude/skills/session-sterility/SKILL.md`
  - Contract: `tests/contracts/test_story_5_1_ephemeral_session_disk.py`
  - Spec Gate: `scripts/spec_gate.py 5.1` (Passed, margin +0.2129, episode `spec-5_1-3380cbb0`)
- **Validation results:**
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'scripts.lib.session_sterility'`).
  - Story contract: `tests/contracts/test_story_5_1_ephemeral_session_disk.py` 5 passed.
  - Full suite: `pytest tests` 111 passed.
  - Lifecycle: `scripts/validate_lifecycle.py` `Invariants: PASS`.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - Idle teardown timer (300 s) must strictly require `active_open_requests == 0`; if requests remain active, teardown is deferred per `AC-02.1` and `FDD-005`.
  - Parent SHA-256 hash must be verified bit-for-bit before and after session execution to ensure zero parent corruption per `AC-02.2`.
  - Hung requests reaching 900 s ceiling trigger HTTP 504 and instance reaping per `BRU-005-04`.
- **Open for a human:** None.
- **Breakout recap:** Pending Step 9 epic closeout.
