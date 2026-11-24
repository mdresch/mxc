---
artifact_id: schedule-foundation-activity-list
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-2A
pmbok_process: Develop Schedule — define activities
depends_on:
  - 6.B-1
  - 6.B-2
---

# Schedule Activity List — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Decomposed into asynchronous agent-executable tasks corresponding to approved User Stories (Stories 1.1 through 6.4) from the WBS Dictionary.

## Activity breakdown and agent execution contracts

| Activity ID | WBS ID | Story ID | Activity / deliverable | Predecessors | Agent role | Tooling & contracts | Verification & exit gate |
|---|---|---|---|---|---|---|---|
| **ACT-01** | 1.0 | — | Scope and WBS Baseline Reconciliation | None | Coordinator | Repo docs, `validate_lifecycle.py` | `approve-pmp` review pass |
| **ACT-02** | 2.1 | Story 1.1 | Gen 2 VM Provisioning & Boundary | None | Platform Worker | Hyper-V PowerShell, `wxc-exec` | `spec_gate` -> VM Gen 2 check -> `pr_gate` |
| **ACT-03** | 2.2 | Story 1.2 | In-Guest Windows Subsystems Validation | ACT-02 | Platform Worker | Guest WMI, COM+, WinServices probe | In-guest test execution -> `pr_gate` |
| **ACT-04** | 4.1 | Story 3.1 | Clean Production VHDX Bake Pipeline | ACT-02 | Release Worker | PowerShell bake script, filesystem scanner | Image audit scanner (0 dev tools) -> `pr_gate` |
| **ACT-05** | 4.2 | Story 3.2 | Warm Baseline Checkpoint Capture | ACT-03, ACT-04 | Release Worker | Health probe, DB handle reset, Hyper-V snapshot | `baseline-hot-ready` checkpoint verified |
| **ACT-06** | 6.2 | Story 5.2 | Network Airgap & Egress Whitelist | ACT-02 | Security Worker | Hyper-V VSwitch Port ACL automation | TCP port probe (public deny, internal allow) |
| **ACT-07** | 5.1 | Story 4.1 | Zero Idle CPU & GPU Suspension | ACT-05 | Platform Worker | `Suspend-VM`, PerfMon counter collector | Host PerfMon reads 0.0% CPU/GPU across pool |
| **ACT-08** | 5.2 | Story 4.2 | Memory Working Set Pre-Trimming | ACT-05, ACT-07 | Platform Worker | Working set trimmer, RAM counter probe | Paused host RAM commit within target |
| **ACT-09** | 5.3 | Story 4.3 | Sub-300ms Resume-VM Latency | ACT-07 | Platform Worker | `Resume-VM` timing benchmark script | Benchmarks show $\le 300\text{ms}$ unpause |
| **ACT-10** | 6.1 | Story 5.1 | Ephemeral Differencing Disk Lifecycle | ACT-05 | Security Worker | Differencing VHDX attach/detach script | Deletion on session close, parent hash bit-identical |
| **ACT-11** | 6.3 | Story 5.3 | Discard & Reproduce Path Verification | ACT-10 | Security Worker | Side-by-side session recreation test | Verification of Path A (VM) & Path B (.avhdx) |
| **ACT-12** | 3.1 | Story 2.1 | Connection-Buffering Ingress & Hold | ACT-09, ACT-10 | Gateway Worker | Ingress HTTP proxy, socket hold, `mxc-pool-lease` | TTFB $\le 800\text{ms}$, platform wake $\le 300\text{ms}$ |
| **ACT-13** | 3.2 | Story 2.2 | Ingress Saturation & 503 Fallback | ACT-12 | Gateway Worker | Timeout handler, structured HTTP 503 producer | 0 wake 502/504s under load; 503 Retry-After on timeout |
| **ACT-14** | 3.3 | Story 2.3 | Path & Port Dual Routing Rules | ACT-12 | DevOps Worker | Reverse proxy route dispatcher | Independent path and port selection verified |
| **ACT-15** | 7.3 | Story 6.3 | In-Guest Wake Hygiene & PRNG Reset | ACT-05, ACT-09 | SRE Worker | `RDRAND`, `ClearAllPools`, host UTC sync | First `/health` call verifies clock, PRNG, and DB pools |
| **ACT-16** | 7.1 | Story 6.1 | Instant Background Buffer Replenish | ACT-12 | SRE Worker | Asynchronous background worker thread | New guest in `StandbyPaused` $\approx 1.5\text{s}$ post-lease |
| **ACT-17** | 7.2 | Story 6.2 | Concurrency Surge Dynamic Expansion | ACT-16 | SRE Worker | Velocity burst autoscaler script | Buffer expands up to $K_{\text{max}}$ on $>10\text{ req/s}$ |
| **ACT-18** | 7.4 | Story 6.4 | Idle Fleet Scale-Down & Reclamation | ACT-17 | SRE Worker | Fleet reaper background service | Surplus VMs deallocated after 180s/300s cooldown |
| **ACT-19** | 8.0 | — | Integrated End-to-End Acceptance | ACT-03, ACT-06, ACT-08, ACT-11, ACT-13, ACT-14, ACT-15, ACT-18 | Test Coordinator | Test harness, synthetic user workload | Full operational demonstration of all 12 benefits |

## Agent concurrency and collision avoidance

1. **Autonomous Pickup Protocol**:
   - Asynchronous agent workers claim tasks matching their assigned role by recording a lease in `docs/registers/Story-Execution-Register.md` or opening a dedicated branch `feat/story-<num>`.
   - Before implementation, workers execute `python scripts/spec_gate.py --story <id>`. If pre-flight checks fail, the worker pauses to amend specification or request clarification.
2. **Parallel Concurrency Waves**:
   - **Wave 1 (Parallel Foundation)**: ACT-02 (Gen 2 boundary), followed concurrently by ACT-03, ACT-04, and ACT-06.
   - **Wave 2 (Standby & Ephemeral State)**: ACT-05 -> ACT-07 -> ACT-08, ACT-09 in parallel with ACT-10, ACT-11.
   - **Wave 3 (Ingress & Gateway)**: ACT-12 -> ACT-13 and ACT-14 in parallel with ACT-15.
   - **Wave 4 (Autoscaling & SRE)**: ACT-16 -> ACT-17 -> ACT-18.
   - **Wave 5 (Acceptance & Roll-Up)**: ACT-19.
