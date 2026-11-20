---
artifact_id: scope-foundation-validate-scope
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.A-4
pmbok_process: Validate Scope
depends_on:
  - 6.A-1
  - 6.A-2
---

# Validate Scope — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Validation evidence demonstrates acceptance; it does not replace formal human approval. Source BRDs are approved, but the Charter and integrated PMP approval state need reconciliation.

## Acceptance and verification matrix

| WBS ID | Deliverable / work package | Acceptance criteria source | Verification method | Reviewer / approver | Evidence location |
|---|---|---|---|---|---|
| **2.0** | **Isolated Generation 2 guest** | BRD-001; Epic 001 | Guest subsystem and isolation checks | Platform Lead | Tests / execution evidence TBD |
| 2.1 | Generation 2 isolation boundary | Story 1.1; BRU-001-02 | PowerShell hypervisor inspection of VM generation and kernel | Platform Engineer | `scripts/hyperv/` verification tests |
| 2.2 | Windows subsystems on guest | Story 1.2; BEN-05 | In-guest execution probes of WMI, COM+, Services, Group Policy | Release Engineer | Guest execution probe logs |
| **3.0** | **Connection-buffering ingress and wake** | BRD-002; Epic 002 | Cold-wake timing, routing, HTTP result checks | Gateway Lead | Gateway logs / tests TBD |
| 3.1 | Cold wake TTFB & connection hold | Story 2.1; AC-01.1; BEN-02 | Benchmark client measuring TTFB $\le 800\text{ms}$ and wake $\le 300\text{ms}$ | Gateway Engineer | `benchmark_jit_wake.py` output |
| 3.2 | Saturation handling & zero wake errors | Story 2.2; AC-01.3; BEN-03 | Synthetic traffic load test ensuring 0 502/504s; 503 on timeout | Gateway Engineer | Ingress gateway stress logs |
| 3.3 | Dual routing rules (path & port) | Story 2.3; HYP-mxc-004; BEN-04 | Separate test requests to `/api/v1/adpa` and `:8091` listener | DevOps Engineer | Routing telemetry logs |
| **4.0** | **Production image and warm checkpoint** | BRD-003; Epic 003 | Image inventory, hash, and health-checkpoint inspection | Image Lead | Image catalog / bake evidence TBD |
| 4.1 | Clean production VHDX image bake | Story 3.1; AC-04.1; BEN-08 | Automated audit script scanning VHDX filesystem for build tools | Release Engineer | Image audit scorecard output |
| 4.2 | Warm baseline checkpoint capture | Story 3.2; AC-04.2 | Smoke test against `/health`, DB pool check, memory snapshot | Release Engineer | Baking pipeline execution log |
| **5.0** | **Paused standby and footprint** | BRD-004; Epic 004 | CPU/GPU/RAM/disk readings and resume timing | Platform Lead | Host measurement evidence TBD |
| 5.1 | Zero idle CPU & GPU enforcement | Story 4.1; AC-03.1; BEN-01 | Host PerfMon counters reading 0.0% CPU/GPU across paused pool | Platform Engineer | Host telemetry logs |
| 5.2 | Trimmed paused footprint | Story 4.2; AC-03.2; BEN-10 | Host commit memory measurement of paused guest instances | Platform Engineer | Memory profile recordings |
| 5.3 | Sub-300ms hypervisor resume | Story 4.3; AC-03.3; BEN-02 | Hyper-V `Resume-VM` timing benchmark | Platform Engineer | Platform latency benchmarks |
| **6.0** | **Session sterility and egress control** | BRD-005; Epic 005 | Discard tests, parent hash check, allow/deny probes | Security Lead | Security test evidence TBD |
| 6.1 | Ephemeral session disk lifecycle | Story 5.1; AC-02.1; AC-02.2; BEN-07 | Differencing disk deletion check, SHA-256 parent hash match | SecOps Engineer | Session teardown logs |
| 6.2 | Network airgap & egress whitelist | Story 5.2; AC-02.3; BEN-07 | TCP port probe against public IP and internal allowlist | SecOps Engineer | VSwitch port ACL test logs |
| 6.3 | Discard and reproduce verification | Story 5.3; BEN-12 | Side-by-side run of Path A (VM recreation) and Path B (.avhdx) | SecOps Engineer | Session reproduction logs |
| **7.0** | **Pool replenishment and wake hygiene** | BRD-006; Epic 006 | Lease/refill, health, entropy/clock/pool checks | SRE Lead | Integration test evidence TBD |
| 7.1 | Instant buffer replenishment | Story 6.1; AC-05.1 | Asynchronous pool lease and refill timer measurement | SRE / DevOps | Pool manager logs |
| 7.2 | Dynamic surge expansion | Story 6.2; AC-05.2; BEN-09 | Concurrency burst generator evaluating buffer expansion to K_max | SRE / DevOps | Autoscaler load test reports |
| 7.3 | Wake hygiene & clock/pool reset | Story 6.3; AC-02.4; BEN-09 | In-guest `/health` probe verifying entropy, DB pools, clock sync | SRE / DevOps | Guest service wake logs |
| 7.4 | Fleet scale-down and memory reclamation | Story 6.4; AC-05.4 | Idle timeout test verifying surplus guest reaping | SRE / DevOps | Fleet reaper logs |
| **8.0** | **Integrated acceptance** | BRD-001 through BRD-006; USER_STORIES.md | End-to-end test against resolved criteria | Test Lead | Release evidence TBD |

## Definition of done

Minimum completion evidence includes a stable WBS/requirement link, repeatable test or inspection output, reviewer disposition, defect disposition, and a traceable governance record. The test owner and evidence retention location remain to be assigned.

## Requirements traceability

Use approved BRD-001 through BRD-006 and their linked architecture/user-story criteria as requirement sources. Record the exact criterion, test result, environment, date, and human acceptance decision. The `docs/hyperv/architecture/USER_STORIES.md` suite is the current story source.

## Rejection and rework

Record rejected deliverables as open issues with the failed criterion, owner, corrective action, and re-test evidence. Re-verify against the unchanged approved criterion; a changed criterion requires the relevant governance approval before acceptance.
