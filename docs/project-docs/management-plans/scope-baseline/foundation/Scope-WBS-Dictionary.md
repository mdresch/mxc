---
artifact_id: scope-foundation-wbs-dictionary
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.A-2
pmbok_process: Develop Scope Structure
depends_on:
  - 6.A-1
---

# Scope WBS and Dictionary — MXC Hyper-V for ADPA / SIDPA

**Status:** Proposed WBS for review only. The Charter was approved on 2026-10-30; this is neither an approved scope baseline nor an execution schedule.

## Decomposition rules

Decompose to observable deliverables traced to BRD-001 through BRD-006. The entries below are top-level work packages pending owner decomposition. Use lower-level packages only after the scope statement is authorized. Duration, cost, and resource estimates belong in their respective baselines and are intentionally absent.

## Work breakdown structure

| WBS ID | Parent | Deliverable / work package | Included work | Exclusions / interface | Acceptance source | Owner | Status |
|---|---|---|---|---|---|---|---|
| **1.0** | — | **Governed project scope and requirements trace** | Charter reconciliation, scope baseline, traceability, decision records | Does not authorize implementation | Project Charter; PMP gate | Project owner | draft |
| **2.0** | — | **Isolated Hyper-V guest** | Dedicated Generation 2 guest isolation boundary and Windows automation subsystem runtime | Does not include shared-kernel containers | ADR-001; BRD-001; Epic 001 | Platform Lead | draft |
| 2.1 | 2.0 | Generation 2 isolation boundary | Hyper-V Gen 2 VM provisioning, UEFI firmware validation, distinct host/guest kernel separation, container rejection logic | Shared-kernel containers strictly excluded | Story 1.1; BRU-001-02 | Platform Engineer | ready for review |
| 2.2 | 2.0 | Windows subsystems on guest | In-guest execution support for WMI, COM+, dedicated Windows Services, and Group Policy enforcement | Non-Windows guest environments | Story 1.2; BEN-05 | Release Engineer | ready for review |
| **3.0** | — | **Connection-buffering ingress and wake** | Asynchronous HTTP connection holding, dual routing dispatch, cold wake orchestration | Does not include global edge CDN or external DNS | ADR-002; BRD-002; Epic 002 | Gateway Lead | draft |
| 3.1 | 3.0 | Cold wake TTFB & connection hold | HTTP request socket holding, fast wake triggering via `mxc-pool-lease`, sub-300ms wake, sub-800ms Time to First Byte | Warm request proxying | Story 2.1; AC-01.1; BEN-02 | Gateway Engineer | ready for review |
| 3.2 | 3.0 | Saturation handling & zero wake errors | Zero HTTP 502/504 errors on dormant wake; structured HTTP 503 Service Unavailable with `Retry-After` on timeout | Long-running socket leaks (>900s) | Story 2.2; AC-01.3; BEN-03 | Gateway Engineer | ready for review |
| 3.3 | 3.0 | Dual routing rules (path & port) | Independent evaluation of path routing (`/api/v1/adpa` -> `prod-adpa`) and catalogued listener ports (`:8091` -> ADPA image) | Combined single-rule matching | Story 2.3; HYP-mxc-004; BEN-04 | DevOps Engineer | ready for review |
| **4.0** | — | **Production image and warm checkpoint** | Headless base image build pipeline, toolchain sanitization audit, warm health checkpoint | Development tool installation in prod | ADR-003; BRD-003; Epic 003 | Image Lead | draft |
| 4.1 | 4.0 | Clean production VHDX image bake | Automated baking script and audit pipeline verifying complete absence of compilers, git, cargo, uv, Scoop, and repos | Development SDKs/compilers | Story 3.1; AC-04.1; BEN-08 | Release Engineer | ready for review |
| 4.2 | 4.0 | Warm baseline checkpoint capture | In-guest ADPA/SIDPA service startup, `localhost:8080/health` probe, DB pool clearing, `baseline-hot-ready` memory checkpoint | Unpre-warmed cold disks | Story 3.2; AC-04.2 | Release Engineer | ready for review |
| **5.0** | — | **Paused standby and footprint** | Hypervisor standby state management, memory working set trimming, rapid resume | Standby disk teardown | ADR-004; BRD-004; Epic 004 | Platform Lead | draft |
| 5.1 | 5.0 | Zero idle CPU & GPU enforcement | Suspend guest execution to Hyper-V `Paused` state; verify 0.0% CPU and 0.0% GPU load on host monitor | Active request execution | Story 4.1; AC-03.1; BEN-01 | Platform Engineer | ready for review |
| 5.2 | 5.0 | Trimmed paused footprint | Working set pre-trimming before snapshot capture; hold paused host RAM footprint within target boundary | Uncompressed guest memory | Story 4.2; AC-03.2; BEN-10 | Platform Engineer | ready for review |
| 5.3 | 5.0 | Sub-300ms hypervisor resume | Rapid hypervisor unpause via `Resume-VM` executing in $\le 300\text{ms}$ platform latency | In-guest request dispatch | Story 4.3; AC-03.3; BEN-02 | Platform Engineer | ready for review |
| **6.0** | — | **Session sterility and egress control** | Differencing delta disk lifecycle, network airgap ACLs, session cleanup and reproduction | Permanent in-guest data writes | ADR-005; BRD-005; Epic 005 | Security Lead | draft |
| 6.1 | 6.0 | Ephemeral session disk lifecycle | Differencing disk (`.avhdx`) attachment per session; automated deletion upon session close or 300s idle; parent VHDX SHA-256 integrity | Permanent delta persistence | Story 5.1; AC-02.1; AC-02.2; BEN-07 | SecOps Engineer | ready for review |
| 6.2 | 6.0 | Network airgap & egress whitelist | Hyper-V virtual switch port ACLs blocking public internet; whitelisting SQL :1433, Postgres :5432, Blob :443, DNS :53, Kerberos :88 | Public internet connectivity | Story 5.2; AC-02.3; BEN-07 | SecOps Engineer | ready for review |
| 6.3 | 6.0 | Discard and reproduce verification | Dual session termination validation: Path A whole-guest teardown and Path B differencing disk discard with clean parent reproduction | Cross-session state inheritance | Story 5.3; BEN-12 | SecOps Engineer | ready for review |
| **7.0** | — | **Pool replenishment and wake hygiene** | Standby buffer manager, concurrency burst autoscaling, entropy re-seeding, scale-down reaper | Manual pool provisioning | ADR-006; BRD-006; Epic 006 | SRE Lead | draft |
| 7.1 | 7.0 | Instant buffer replenishment | Background asynchronous promotion/spin-up of next standby VM into `StandbyPaused` within ~1.5s after lease event | In-flight request thread | Story 6.1; AC-05.1 | SRE / DevOps | ready for review |
| 7.2 | 7.0 | Dynamic surge expansion | Velocity autoscaler expanding standby buffer up to $K_{\text{max}}$ upon $> 10\text{ req/s}$ surge or queue depth $> 0$ | Static pool configurations | Story 6.2; AC-05.2; BEN-09 | SRE / DevOps | ready for review |
| 7.3 | 7.0 | Wake hygiene & clock/pool reset | Hardware PRNG re-seeding (`RDRAND`/`BCryptGenRandom`), ADO.NET/Npgsql connection pool flushing, host UTC clock sync | Stale TCP pools / clock skew | Story 6.3; AC-02.4; BEN-09 | SRE / DevOps | ready for review |
| 7.4 | 7.0 | Fleet scale-down and memory reclamation | Idle reaper evaluating fleet after 180s/300s inactivity, deallocating surplus instances back to $K_{\text{min}}$ | Active session termination | Story 6.4; AC-05.4 | SRE / DevOps | ready for review |
| **8.0** | — | **Integrated acceptance evidence** | Cross-package integration testing, verification evidence aggregation, and operational demonstration | Individual unit mocks | BRD-001..006; USER_STORIES.md | Test Lead | draft |

## Dictionary completeness checks

- Each work package has a unique stable identifier and one accountable owner.
- Deliverables cover the approved scope without overlap or unexplained gaps.
- Requirements and acceptance sources are traceable.
- Estimates and execution authorization are not implied by this dictionary.

## Open decomposition issues

| ID | Issue | Affected WBS | Owner | Status |
|---|---|---|---|---|
| Q-WBS-001 | Confirm WBS ownership and decomposition level after Charter approval | All | Project owner | open |
| Q-WBS-002 | Reconcile unresolved RAM, surge, and routing acceptance rules | 3.0, 5.0, 7.0 | Project owner | open |
| Q-WBS-003 | Add lower-level work packages from approved stories without introducing unsupported estimates | 2.1–7.4 | Project owner | resolved (Stories 1.1–6.4 mapped to WBS 2.1–7.4) |
