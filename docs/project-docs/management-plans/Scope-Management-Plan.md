---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.1 Scope Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Benefits-Statement.md"
  - "../../hyperv/architecture/BRD-001.md through BRD-006.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
process: "Define how project scope is developed, validated, and controlled across WBS 1.0–8.0"
outputs:
  - "Scope-Management-Plan.md"
  - "scope-baseline/foundation/Scope-Project-Scope-Statement.md"
  - "scope-baseline/foundation/Scope-WBS-Dictionary.md"
  - "scope-baseline/foundation/Scope-Validate-Scope.md"
status: "Approved"
---

# Scope Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the authorized Scope Baseline (`PMP-BL-v1.0.0`) grounded in approved technical requirements (BRD-001–006 and Stories 1.1–6.4).

## 1. Executive summary and scope management approach

This Scope Management Plan defines how the project scope is defined, structured, validated, and controlled for MXC Phase 1. 

Scope planning is built upon the **6 Topic Pillars (TP-01 through TP-06)** and decomposes into 8 top-level WBS deliverables and 17 atomic, agent-executable work packages:
- **WBS 1.0**: Governed Project Scope and Requirements Trace
- **WBS 2.0**: Dedicated Generation 2 Hyper-V Guest Isolation Boundary (Stories 1.1, 1.2)
- **WBS 3.0**: Connection-Buffering Ingress & Protocol Router (Stories 2.1, 2.2, 2.3)
- **WBS 4.0**: Clean Production Image Supply & Warm Checkpoint Pipeline (Stories 3.1, 3.2)
- **WBS 5.0**: Paused Standby Footprint & Rapid Resume (Stories 4.1, 4.2, 4.3)
- **WBS 6.0**: Session Sterility & Egress Control (Stories 5.1, 5.2, 5.3, 6.4)
- **WBS 7.0**: Pool Replenishment & Wake Hygiene (Stories 6.1, 6.2, 6.3, 6.4)
- **WBS 8.0**: Integrated Phase 1 Acceptance Gate (All 12 Charter Benefits)

---

## 2. Scope foundation pack structure

The complete scope baseline model is documented in the foundation pack:
1. **Pillar Overview and Trace**: [Scope-Pillar-Overview-and-Trace.md](scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md) traces outcomes to WBS packages and Milestones M1 through M5.
2. **Project Scope Statement**: [Scope-Project-Scope-Statement.md](scope-baseline/foundation/Scope-Project-Scope-Statement.md) documents deliverables, exclusions, and reconciled parameters ($\le 700\text{MB}$ RAM commit, $> 10\text{ req/s}$ surge window).
3. **WBS & WBS Dictionary**: [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) decomposes packages 1.0 through 8.0, mapping 1:1 to approved User Stories.
4. **Scope Validation Protocol**: [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md) defines BDD verification methods, test harnesses, and acceptance reviewers.
5. **Monitor & Control Scope**: [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md) establishes variance controls, change workflows, and audit protocols.
6. **Domain Checklist**: [Scope-Domain-Checklist.md](scope-baseline/foundation/Scope-Domain-Checklist.md) confirms PMBOK 8 Scope Performance Domain compliance (**PASS**).

---

## 3. Scope validation and acceptance procedure

1. **Pre-Implementation Specification Check**:
   - Before implementing any work package, workers execute `python scripts/spec_gate.py --story <id>` to ensure prerequisites and acceptance definitions are satisfied.
2. **Acceptance Verification**:
   - Each work package deliverable is verified against its exact BDD acceptance criteria documented in [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md).
   - Verification execution is logged and evaluated via `python scripts/pr_gate.py --pr <pr_num>`.
3. **Formal Scope Sign-Off**:
   - The Operational Benefit Owner (Menno Drescher) and Quality Coordinator formally sign off on Phase 1 acceptance upon passing WBS 8.0 end-to-end integration tests.
