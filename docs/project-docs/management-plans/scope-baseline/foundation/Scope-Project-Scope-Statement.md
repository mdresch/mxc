---
artifact_id: scope-foundation-project-scope-statement
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.A-1
pmbok_process: Define Scope
depends_on:
  - 6.A-0P
---

# Project Scope Statement — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft — Ready for Baseline Review. Reconciled against the approved Project Charter, approved Benefits Statement, and approved technical requirements (BRD-001–006 and Stories 1.1–6.4).

## 1. Purpose and project objectives

The approved [Project Charter](../../Project-Charter.md) and [Benefits Statement](../../Benefits-Statement.md) authorize delivery of a just-in-time, scale-to-zero production Hyper-V sandbox environment for ADPA and SIDPA workloads. MXC replaces heavy 24/7 dedicated virtual machines with lightweight, ephemeral Generation 2 Hyper-V guests that pause to zero CPU/GPU footprint and resume on demand in under 300 ms, presenting a zero-cold-start illusion via connection-buffering ingress.

---

## 2. Product and project scope description

The scope encompasses 8 core deliverable areas decomposed into 17 atomic, test-verified work packages:

1. **Governed Project Scope and Requirements Trace (WBS 1.0)**: Complete traceability matrix connecting Charter objectives, BRDs, ADRs, User Stories, and PMBOK subsidiary plans.
2. **Dedicated Generation 2 Guest Isolation (WBS 2.0)**:
   - *WBS 2.1 (Story 1.1)*: Type-1 Hyper-V Generation 2 VM boundary with UEFI firmware and hardware virtualization (shared-kernel containers strictly excluded).
   - *WBS 2.2 (Story 1.2)*: Full Windows guest fidelity supporting WMI, COM+, dedicated Windows Services, and Group Policy enforcement.
3. **Connection-Buffering Ingress & Protocol Router (WBS 3.0)**:
   - *WBS 3.1 (Story 2.1)*: Asynchronous HTTP socket holding delivering $\le 800\text{ms}$ Time to First Byte (TTFB) and sub-300ms platform wake.
   - *WBS 3.2 (Story 2.2)*: Zero wake-induced HTTP 502/504 errors; structured HTTP 503 `Retry-After` on pool exhaustion timeout.
   - *WBS 3.3 (Story 2.3)*: Independent evaluation of path routing (`/api/v1/adpa`) and catalogued listener ports (`:8091`).
4. **Clean Production Image Supply & Warm Checkpoint (WBS 4.0)**:
   - *WBS 4.1 (Story 3.1)*: Headless automated VHDX bake pipeline verified zero compilers, git, cargo, uv, or source repositories.
   - *WBS 4.2 (Story 3.2)*: Pre-warmed `baseline-hot-ready` memory checkpoint captured after guest health probe and DB pool clearing.
5. **Paused Standby Footprint & Rapid Resume (WBS 5.0)**:
   - *WBS 5.1 (Story 4.1)*: Hypervisor suspension verifying 0.0% CPU and 0.0% GPU consumption on host monitors.
   - *WBS 5.2 (Story 4.2)*: Working set pre-trimming guaranteeing paused host RAM commit $\le 700\text{MB}$ per standby guest.
   - *WBS 5.3 (Story 4.3)*: Hyper-V `Resume-VM` latency executing in $\le 300\text{ms}$.
6. **Session Sterility & Egress Control (WBS 6.0)**:
   - *WBS 6.1 (Story 5.1)*: Ephemeral differencing disk (`.avhdx`) discarded on session close; golden parent VHDX remains bit-identical (SHA-256 matched).
   - *WBS 6.2 (Story 5.2)*: Hyper-V virtual switch Port ACLs enforcing strict airgap (public internet blocked; internal DB/blob whitelisted).
   - *WBS 6.3 (Story 5.3)*: Automated verification of Path A (VM recreation) and Path B (differencing disk discard).
7. **Pool Replenishment & Wake Hygiene (WBS 7.0)**:
   - *WBS 7.1 (Story 6.1)*: Background asynchronous replenish thread restoring standby buffer in $\approx 1.5\text{s}$ post-lease.
   - *WBS 7.2 (Story 6.2)*: Velocity autoscaler dynamically expanding standby buffer up to $K_{\text{max}}$ upon $> 10\text{ req/s}$ surge.
   - *WBS 7.3 (Story 6.3)*: In-guest wake hygiene re-seeding PRNG (`RDRAND`), clearing DB connection pools, and syncing host UTC time.
   - *WBS 7.4 (Story 6.4)*: Idle fleet reaper deallocating surplus standby instances after 180s/300s cooldown.
8. **Integrated Phase 1 Acceptance Gate (WBS 8.0)**: Multi-session automated acceptance test suite demonstrating all 12 Charter benefits.

---

## 3. Product exclusions and explicit non-goals

| Excluded item | Reason / authority | Reconsideration trigger |
|---|---|---|
| **Future research hypotheses HYP-mxc-015 through 020** | Excluded from Phase 1 scope by the approved Business Case | Phase 2 charter review and explicit scope authorization |
| **Shared-Kernel Windows Containers** | Architectural decision ADR-001 (insufficient kernel boundary for untrusted agents) | Never; Gen 2 VM isolation is a non-negotiable invariant |
| **Production Image Code Signing / Vulnerability Scanning** | Deferred to future deployment pipeline in BRD-003 | Production deployment hardening phase |
| **Public Internet Egress for Sandboxed Guests** | Security requirement ADR-005 / BRD-005 | Security policy amendment approved by Steering Committee |
| **Global Edge Anycast DNS / Multi-Region Ingress** | Out of scope for single-host Phase 1 prototype | Phase 2 multi-host distributed cluster expansion |

---

## 4. Constraints, assumptions, and reconciled technical parameters

1. **Paused RAM Target**: Formally reconciled to **$\le 700\text{MB}$ commit** per guest (ADR-004, Story 4.2). The higher initial estimates (~1.0–1.2 GB) reflect untrimmed boot states prior to memory working-set optimization.
2. **Surge Measurement Window**: Formally defined as an incoming request arrival velocity $> 10\text{ req/s}$ or lease queue depth $> 0$ over a rolling 5-second sampling window (Story 6.2).
3. **Dual Routing Independence**: Path-based pool routing (`/api/v1/adpa`) and listener-port image selection (`:8091`) operate as independent, non-conflicting routing criteria (Story 2.3).
4. **Financial Authority**: Total project budget of \$20,365 is fully within the Project Manager's delegated threshold of \$25,000.
