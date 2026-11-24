---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "6.1 Schedule Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
process: "Decomposed across 19 activities and 5 asynchronous execution waves matching approved WBS 1.0–8.0 and Stories 1.1–6.4"
outputs:
  - "Schedule-Management-Plan.md"
  - "schedule-baseline/foundation/Schedule-Activity-List-Phase1.md"
  - "schedule-baseline/foundation/Schedule-Network-Phase1.md"
  - "schedule-baseline/foundation/Schedule-Gantt-Phase1.md"
  - "schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md"
status: "Approved"
---

# Schedule Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the authorized Schedule Baseline (`PMP-BL-v1.0.0`) decomposed at agentic granularity across 5 execution waves.

## 1. Purpose and scope

This Schedule Management Plan establishes the scheduling methodology, measurement units, critical path logic, asynchronous concurrency rules, and variance thresholds for MXC Phase 1. It operates in strict alignment with:
- The [Scope Management Plan](Scope-Management-Plan.md) and [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) (WBS 1.0 through 8.0, Stories 1.1 through 6.4).
- The 6 Topic Pillars (TP-01 Isolation, TP-02 Ingress, TP-03 Image supply, TP-04 Paused footprint, TP-05 Session sterility, TP-06 Pool and wake hygiene).

---

## 2. Schedule foundation artifacts

The complete schedule baseline model is documented in the foundation pack:
1. **Pillar Overview and Trace**: [Schedule-Pillar-Overview-and-Trace.md](schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md) traces outcomes to Milestones M1 through M5.
2. **Basis of Estimates**: [Schedule-Basis-of-Estimates.md](schedule-baseline/foundation/Schedule-Basis-of-Estimates.md) defines agent turn metrics, execution runtimes, and gate review latencies.
3. **Activity List**: [Schedule-Activity-List-Phase1.md](schedule-baseline/foundation/Schedule-Activity-List-Phase1.md) defines discrete activities (`ACT-01` to `ACT-19`) with agent roles and validation gates.
4. **Schedule Network**: [Schedule-Network-Phase1.md](schedule-baseline/foundation/Schedule-Network-Phase1.md) provides the Mermaid dependency diagram, predecessor/successor logic, and critical path analysis.
5. **Gantt & Wave Model**: [Schedule-Gantt-Phase1.md](schedule-baseline/foundation/Schedule-Gantt-Phase1.md) articulates the asynchronous execution waves, early/late times, float, and milestones.
6. **WBS Duration Forecast**: [Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md) details three-point PERT estimates and turn budgets.
7. **Reserve Register**: [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) details contingency reserves ($8.5\text{h}$) and management reserves ($6.5\text{h}$).
8. **Domain Checklist**: [Schedule-Domain-Checklist.md](schedule-baseline/foundation/Schedule-Domain-Checklist.md) confirms PMBOK 8 schedule domain compliance.

---

## 3. Asynchronous agent execution framework

To allow autonomous agent workers to safely pick up tasks and proceed without human bottlenecks or collisions:

1. **Role-Based Task Assignment**:
   - Activities specify the required agent role (Platform Worker, Security Worker, Release Worker, Gateway Worker, SRE Worker, Test Coordinator).
   - Workers select available unblocked tasks from [Schedule-Activity-List-Phase1.md](schedule-baseline/foundation/Schedule-Activity-List-Phase1.md).
2. **Pre-Implementation Spec Gate**:
   - The agent runs `python scripts/spec_gate.py --story <id>`. If predecessor deliverables or specifications are missing, the agent halts before generating code.
3. **Workspace Isolation**:
   - Agents execute within isolated git branches (`feat/story-<num>`) or separate shared worktrees to avoid uncommitted file conflicts.
4. **Post-Implementation PR Gate**:
   - After completing the code and unit tests, the agent runs `python scripts/pr_gate.py --pr <pr_num>`.
   - Successful gate execution automatically signals completion and unblocks downstream activities in the [Schedule Network](schedule-baseline/foundation/Schedule-Network-Phase1.md).

---

## 4. Critical path and performance baseline

- **Primary Critical Path**:
  $$\text{ACT-01} \longrightarrow \text{ACT-02} \longrightarrow \text{ACT-04} \longrightarrow \text{ACT-05} \longrightarrow \text{ACT-07} \longrightarrow \text{ACT-09} \longrightarrow \text{ACT-12} \longrightarrow \text{ACT-16} \longrightarrow \text{ACT-17} \longrightarrow \text{ACT-18} \longrightarrow \text{ACT-19}$$
- **Expected Duration ($T_e$)**: **31.0 clock hours** ($\approx 132$ agent turns).
- **Contingency Reserve**: **8.5 clock hours**.
- **Total Baseline with Contingency**: **39.5 clock hours**.
- **Variance Threshold**: A cumulative schedule variance (SV) $> 20\%$ or critical path delay $> 3.0\text{ hours}$ triggers escalation to the Project Manager.
