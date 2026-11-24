---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
  - "Benefits-Statement.md"
  - "Business-Case.md"
  - "management-plans/Scope-Management-Plan.md"
  - "management-plans/Schedule-Management-Plan.md"
  - "management-plans/Resource-Management-Plan.md"
  - "management-plans/Cost-Management-Plan.md"
  - "management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
  - "management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md"
process: "Integrate approved subsidiary management plans and establish authorized project baselines"
outputs:
  - "Project-Management-Plan.md"
status: "Approved"
---

# Project Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the integrated Project Management Plan baseline **`PMP-BL-v1.0.0`** and authorizes progression toward Stage 8 Implementation Readiness.

## 1. Executive summary and authorization

The [Project Charter](Project-Charter.md) was approved by the Steering Committee on 2026-10-30, and the [Benefits Statement](Benefits-Statement.md) was formally approved on 2026-10-30. On 2026-11-20, Menno Drescher approved the four core subsidiary management plans and their foundational packs, establishing the triple baselines (Scope, Schedule, Cost) along with the Resource Baseline.

### Subsidiary Plans Status Matrix

| Subsidiary plan | PMBOK Process | Governance status | Baseline pack reference |
|---|:---:|:---:|---|
| **Scope Management Plan** | 5.1 | **Approved** | [Scope-Foundation-Pack-Manifest.md](management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md) |
| **Schedule Management Plan** | 6.1 | **Approved** | [Schedule-Foundation-Pack-Manifest.md](management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md) |
| **Resource Management Plan** | 9.1 | **Approved** | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) |
| **Cost Management Plan** | 7.1 | **Approved** | [Cost-Foundation-Pack-Manifest.md](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md) |
| **Quality Management Plan** | 8.1 | **Approved** | [Quality-Management-Plan.md](management-plans/Quality-Management-Plan.md) |
| **Communications Management Plan** | 10.1 | **Approved** | [Communications-Management-Plan.md](management-plans/Communications-Management-Plan.md) |
| **Risk Management Plan** | 11.1 | **Approved** | [Risk-Management-Plan.md](management-plans/Risk-Management-Plan.md) |
| **Procurement Management Plan** | 12.1 | **Approved** | [Procurement-Management-Plan.md](management-plans/Procurement-Management-Plan.md) |
| **Stakeholder Engagement Plan** | 13.1 | **Approved** | [Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md) |

---

## 2. Integrated project baselines (`PMP-BL-v1.0.0`)

### A. Scope Baseline
- **Governing Structure**: WBS 1.0 through 8.0 ([Scope-WBS-Dictionary.md](management-plans/scope-baseline/foundation/Scope-WBS-Dictionary.md)).
- **Decomposition**: 17 atomic, agent-executable work packages directly mapping to approved User Stories (Stories 1.1–6.4) and Technical Architecture decisions (ADR-001 through ADR-007).
- **Core Pillars Covered**: TP-01 Isolation, TP-02 Ingress, TP-03 Image supply, TP-04 Paused footprint, TP-05 Session sterility, TP-06 Pool and wake hygiene.
- **Key Parameters**: Paused RAM commit $\le 700\text{MB}$; surge velocity $> 10\text{ req/s}$; dual routing rules decoupled.

### B. Schedule Baseline
- **Governing Structure**: 19 discrete activities (`ACT-01` to `ACT-19`) sequenced into 5 non-blocking concurrency waves ([Schedule-Network-Phase1.md](management-plans/schedule-baseline/foundation/Schedule-Network-Phase1.md)).
- **Critical Path Duration ($T_e$)**: **31.0 clock hours** ($\approx 132$ agent turns), $\sigma = 1.82\text{h}$.
- **Contingency Reserve**: **8.5 clock hours**.
- **Total Buffered Project Duration**: **39.5 clock hours** ($\approx 170$ agent turns).
- **Milestones**: M1 Platform Ready (11.0h), M2 Sterility Verified (15.8h), M3 Ingress Live (19.5h), M4 Autoscaler Operational (26.8h), M5 Integrated Acceptance (31.0h).

### C. Resource Baseline
- **Human Governance Effort**: **90 person-hours** across 7 specialized engineering/governance roles ([Resource-Capacity-Estimates.md](management-plans/resource-baseline/foundation/Resource-Capacity-Estimates.md)).
- **Autonomous Agent Computation**: **208.8 turns** ($\approx 10.6\text{M tokens}$) across 8 agent worker roles executing within isolated Git branches.
- **Material Sizing**: Dedicated Windows 11 Enterprise Hyper-V host (8–16 cores, 32–64 GB RAM, PCIe Gen 4 NVMe $\ge 2,500\text{ MB/s}$ read, $\ge 150\text{GB}$ differencing pool storage).

### D. Cost Baseline
- **Base Work Package Estimates**: **\$14,665** (90h contractor labor @ blended \$159/hr + \$375 AI tokens) ([Cost-Estimates-by-Category.md](management-plans/cost-baseline/foundation/Cost-Estimates-by-Category.md)).
- **Cost Contingency Reserve (15%)**: **\$2,200**.
- **Total Cost Baseline**: **\$16,865**.
- **Management Reserve**: **\$3,500**.
- **Total Authorized Project Budget**: **\$20,365** (fully within the Project Manager's delegated threshold of **\$25,000**).

---

## 3. Governance, change control, and authority thresholds

1. **Integrated Change Control**:
   - Changes within existing story bounds, schedule float, and budget $\le \$25,000$ are approved by the Project Manager.
   - Any proposed change impacting charter outcomes, adding new architecture pillars, or exceeding USD 25,000 requires formal review and approval by the Steering Committee.
2. **Implementation Gate Handoff**:
   - Approval of this PMP baseline concludes **Stage 7 (Planning: Integrated PMP & Baselines)** and unblocks preparation for **Stage 8 Implementation Readiness**.
   - Workers claim stories via `docs/registers/Story-Execution-Register.md`, run `python scripts/spec_gate.py --story <id>`, and verify implementation via `python scripts/pr_gate.py --pr <pr_num>`.
