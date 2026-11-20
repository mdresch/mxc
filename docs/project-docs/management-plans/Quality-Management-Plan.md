---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "8.1 Quality Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Benefits-Statement.md"
  - "scope-baseline/foundation/Scope-Validate-Scope.md"
  - "scope-baseline/foundation/Scope-WBS-Dictionary.md"
process: "Define quality standards, BDD verification metrics, automated gate rubrics, and acceptance controls"
outputs:
  - "Quality-Management-Plan.md"
status: "Approved"
---

# Quality Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the quality assurance framework, automated gate standards, and BDD verification metrics for MXC Phase 1.

## 1. Quality objectives and acceptance standards

The primary quality objective of MXC is to deliver an enterprise-grade, scale-to-zero production Hyper-V sandbox environment that simultaneously guarantees **zero idle footprint**, **instant sub-second responsiveness**, **total session sterility**, and **uncompromised guest operating system fidelity**.

### Key Technical Quality Metrics

| Dimension | Target standard | Measurement protocol | Verifying WBS & story | Quality owner |
|---|---|---|---|---|
| **Hypervisor Boundary** | 100% Type-1 Hyper-V Gen 2 UEFI; 0 shared-kernel containers | PowerShell VM inspection; firmware descriptor audit | WBS 2.1 (Story 1.1) | Platform Lead |
| **In-Guest Fidelity** | Full native support for WMI, COM+, Services, Group Policy | In-guest execution probes over Hyper-V KVP sockets | WBS 2.2 (Story 1.2) | Platform Lead |
| **Time to First Byte (TTFB)** | $\le 800\text{ms}$ cold request response | Stopwatch proxy benchmark on dormant suspended VM | WBS 3.1 (Story 2.1) | Gateway Lead |
| **Hypervisor Resume Time** | $\le 300\text{ms}$ `Resume-VM` platform unpause | High-resolution kernel timer sweep on host | WBS 5.3 (Story 4.3) | Platform Lead |
| **Zero Wake Errors** | 0 HTTP 502/504 errors on dormant wake; 503 on timeout | Synthetic traffic burst load generator | WBS 3.2 (Story 2.2) | Gateway Lead |
| **Production Image Sanitization** | 0 compilers, git, cargo, uv, Scoop, or source code | Automated VHDX filesystem scanner and audit scorecard | WBS 4.1 (Story 3.1) | Release Lead |
| **Paused Host Memory Footprint** | $\le 700\text{MB}$ commit per suspended guest | Host PerfMon: `Hyper-V Dynamic Memory \ Current Pressure` | WBS 5.2 (Story 4.2) | Platform Lead |
| **Paused Host CPU/GPU Use** | 0.0% CPU and 0.0% GPU consumption in standby | Host PerfMon: `% Total Run Time` across pool | WBS 5.1 (Story 4.1) | Platform Lead |
| **Session Sterility & Isolation** | Differencing disk deleted on close; golden VHDX bit-identical | Automated SHA-256 parent hash comparison | WBS 6.1 (Story 5.1) | Security Lead |
| **Network Airgap Security** | Public internet blocked; internal DB/Blob allowed | TCP port probe suite across public IP and internal allowlist | WBS 6.2 (Story 5.2) | Security Lead |
| **Buffer Replenish Latency** | Standby buffer restored in $\approx 1.5\text{s}$ post-lease | Asynchronous pool manager transition timer | WBS 7.1 (Story 6.1) | SRE Lead |
| **Concurrency Surge Scale** | Dynamic expansion up to $K_{\text{max}}$ upon $> 10\text{ req/s}$ | Velocity autoscaler burst load evaluation | WBS 7.2 (Story 6.2) | SRE Lead |
| **Wake Hygiene Reset** | In-guest PRNG re-seeded (`RDRAND`), DB pools cleared, UTC synced | In-guest `/health` probe post-unpause | WBS 7.3 (Story 6.3) | SRE Lead |

---

## 2. Automated governance and quality gates

Quality assurance is enforced continuously through automated gating tools integrated into the development loop:

```mermaid
flowchart LR
    DEV[Story Branch feat/story-*] --> SPEC["Pre-Flight Gate (spec_gate.py)"]
    SPEC --> CODE[Implement & Unit Test]
    CODE --> PR["Pull Request Gate (pr_gate.py)"]
    PR --> AUDIT["Quality Audit Rubric (5-Point)"]
    AUDIT --> PASS[Merge to Main & Unblock Successors]
```

1. **Pre-Implementation Specification Gate (`scripts/spec_gate.py`)**:
   - Verifies that user story requirements, acceptance criteria, test assertions, and predecessor deliverables exist before implementation begins.
2. **Post-Implementation PR Gate (`scripts/pr_gate.py`)**:
   - Executes unit and integration test suites in Python 3.11 (`pytest`).
   - Evaluates multi-dimensional quality rubrics (Specification Conformance, Contract Consistency, Automated Test Evidence, Topic Pillar Adherence, Lifecycle Invariants).
3. **Lifecycle Conformance Gate (`scripts/validate_lifecycle.py`)**:
   - Enforces SIDPA / PMBOK 8 governance invariants across the 18 lifecycle stages.

---

## 3. Nonconformance and defect triage protocol

1. **Gate Failures**:
   - If an agent worker's PR fails `pr_gate.py`, the agent is granted up to 2 automated repair turns to fix code or test assertions.
   - If still unresolved, the defect is logged in `docs/registers/Implementation-Log.md` and escalated to the Quality & Test Coordinator for human triage via `scripts/lib/review_triage.py`.
2. **Zero Derogation Rule**:
   - Acceptance thresholds (e.g. sub-300ms resume, $\le 700\text{MB}$ RAM, zero build tools in production image) cannot be loosened or waived to achieve a passing test result. Any modification requires a formal scope change under `approve-pmp`.

---

## 4. Final operational acceptance

Final Phase 1 acceptance is governed under WBS 8.0 through a multi-session integration test suite exercising all 17 User Stories and demonstrating all 12 operational benefits from the approved [Benefits Statement](../Benefits-Statement.md). Formal sign-off is recorded by Menno Drescher (Operational Benefit Owner) and the Quality & Test Coordinator.
