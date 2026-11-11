---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "8.1 Plan Quality Management"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-pmp
pmp_baseline: "PMP-BL-v1.0.0"
inputs:
  - "Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "scope-baseline/foundation/Scope-Validate-Scope.md"
  - "Schedule-Management-Plan.md"
process: "Plan and formalize Quality Management Plan"
outputs:
  - "Quality-Management-Plan.md"
---

# Quality Management Plan — mxc

> **PMBOK 8 Process:** `8.1 Plan Quality Management` (Planning)  
> **Governance Policy:** `approve-pmp` (operational subsidiary); foundation packs use `approve-subsidiary-plan` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Project-Charter.md](../Project-Charter.md), approved [Scope Validation Matrix](scope-baseline/foundation/Scope-Validate-Scope.md), [Agentic-Parallel-Execution-Policy.md](../Agentic-Parallel-Execution-Policy.md)

## 1. Purpose & scope

Defines how **mxc** Phase-1 product quality is planned, built in (contract-first), verified, and controlled for WBS **1.1.1–1.6.4** under baseline **`PMP-BL-v1.0.0`**. This plan does **not** authorize execution — **Stage 8** and per-story `implement-story` gates still apply.

## 2. Quality standards

| Standard | Authority | Application |
|---|---|---|
| **Specification acceptance** | [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md) | Per-story AC source = epic/BDD; verification method per row |
| **Contract-first delivery** | ADR/FDD/epic chain 001–006 | Tests/contracts in **RED** before production implementation |
| **Isolation verification** | MXC Hyper-V sandbox | Builds and contract runs in guest VM; host not trusted for product proof |
| **Governance audit trail** | `approve-*` gates, `approve-audit-record` (future) | Material changes escalated per [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md) |
| **Agentic work** | [Agentic-Parallel-Execution-Policy.md](../Agentic-Parallel-Execution-Policy.md) | Tier A/B lanes; agent output is **evidence**, not substitute for human gate on integration |

## 3. Quality gates (Phase 1)

| Gate | Name | Entry criteria | Exit criteria | Owner |
|---|---|---|---|---|
| **QG-01** | Planning baseline | Scope/schedule/resource/cost subsidiary packs approved | Integrated PMP passes **`approve-pmp`** | PM |
| **QG-02** | Work package entry | Story on queue; scope row validated | `validate-intent-foundation` / story readiness per registers | R-QA + lead |
| **QG-03** | Pre-merge verification | Implementation complete in worktree | Contract suite **GREEN**; PR checks pass; no scope drift | R-QA |
| **QG-04** | Release hygiene (pool) | Story touches pool/wake path | Sandbox screenshot or harness evidence where UI/ops behavior matters | R-SRE |

**QG-01 status (2026-11-10):** **Passed** — integrated PMP approved **2026-11-10**.

## 4. Metrics & evidence

| Metric | Target (Phase 1) | Source |
|---|---|---|
| Story AC traceability | 100% WBS rows map to epic AC | Scope validation matrix |
| Contract execution | 100% applicable contracts pass before merge default branch | CI / sandbox test runs |
| Defect escape to integration | Escalate via adaptation if Tier A integration story fails twice | [Story-Execution-Register.md](../../registers/Story-Execution-Register.md) |
| Reserve-trigger quality | SCH-RSV draw requires documented defect or metric breach | [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) |

## 5. Roles

| Role | Quality duty |
|---|---|
| **R-QA** | Gate interpretation, contract RED/GREEN, QG-02/03 sign-off support |
| **R-PLT** | Platform correctness, harness ownership |
| **R-SEC / R-SRE** | Security and reliability acceptance per pillar stories |
| **V-AGT** | Assists implementation; **no** autonomous merge or gate bypass |
| **PM** | Register hygiene, subsidiary plan alignment |

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | [Project-Management-Plan.md](../Project-Management-Plan.md) **§2.8.1**, **§3.5** |
| Upstream scope baseline | Approved **2026-11-10** |
| Lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

Integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Quality planning is verified under **`approve-pmp`**. Approved quality criteria do **not** override Stage 8 execution rules.

**Status:** **Approved (2026-11-10)** — rolled into PMP; formal lock at **`approve-pmp`**.
