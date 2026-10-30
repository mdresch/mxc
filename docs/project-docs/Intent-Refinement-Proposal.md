---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Closing"
pmbok_process: "4.7 Close Project or Phase & Strategic Cognitive Feedback"
pmp_baseline: "PMP-BL-v<X.Y.Z>"
refinement_id: "IR-PROP-v<X.Y.Z>"
lifecycle_stage: "Stage 18 (Intent Refinement)"
governance_policy: "approve-intent-refinement"
readiness_audit_ref: "AUD-REGISTER-v<X.Y.Z>"
disposition_type: "phase_handoff" # "phase_handoff" | "project_termination"
inputs:
  - "docs/project-docs/management-plans/Project-Management-Plan.md"
  - "docs/project-docs/Adaptation-Plan.md"
  - "Actual Outcomes (Stage 12)"
  - "Audit-Register.md"
  - "Lessons Learned Register"
process: "Synthesize empirical outcomes and adaptations to refine top-of-chain intent and resolve hypotheses for subsequent project phases"
outputs:
  - "docs/project-docs/Intent-Refinement-Proposal.md"
  - "docs/project-docs/Spark-Capture.vNext.md" # (omitted if disposition_type == "project_termination")
lineage:
  root_spark: "SPARK-v1.0.0"
  parent_refinement: "IR-PROP-v<PREV.X.Y.Z>"
  generational_index: 2
  immutable_core_invariants:
    - "ADR-001: Decision Authority Model"
    - "ADR-002: Five-Record-Type Storage Boundary"
    - "ADR-005: Decision Progress Comparison"
    - "ADR-008: PMBOK 8 Lifecycle Orchestration"
    - "ADR-009: Double-Loop Cybernetic Loop Closure"
  accumulated_knowledge_hash: "sha256:<hash>"
---

# Intent Refinement Proposal — <Project Name>

> **PMBOK 8 Process:** `4.7 Close Project or Phase & Strategic Cognitive Feedback` (Closing)  
> **Governance Policy:** `approve-intent-refinement` | **Lifecycle Stage:** `Stage 18 (Intent Refinement)`  
> **Governing Baseline:** `PMP-BL-v<X.Y.Z>` | **Refinement ID:** `IR-PROP-v<X.Y.Z>`  
> **Readiness Audit Reference:** `AUD-REGISTER-v<X.Y.Z>` | **Disposition Type:** `phase_handoff`  
> **Inputs:** Project-Management-Plan.md, Adaptation-Plan.md, Actual Outcomes (Stage 12), Audit-Register.md, Lessons Learned  
> **Process:** Synthesize empirical outcomes and adaptations to refine top-of-chain intent and resolve hypotheses  
> **Outputs:** Intent-Refinement-Proposal.md (Catalyst for next Spark Capture)

---

## 1. Executive Evaluation Brief
<Concise summary of phase achievements, realized business value, and strategic variance against original intent. Evaluates whether the phase achieved its core purpose and notes whether this proposal represents a standard phase handoff or formal project termination.>

---

## 2. Phase Close Readiness Gate Checklist (Invariant 7)
- [ ] **Work Packages Closed:** 100% of Stage 8 Work Packages for this baseline are `COMPLETED` or `FORMALLY_DEFERRED`.
- [ ] **Verification Passed:** 100% of Stage 9 Deliverables have passed Stage 10 Verification Evidence with zero critical test failures.
- [ ] **Audit Findings Resolved:** All Stage 11 Audit Records are `APPROVED` with zero unresolved blocker findings.
- [ ] **Operational Quiescence:** No Stage 17 Adaptation Plans are actively mid-execution.

---

## 3. Outcome Delta Evaluation Matrix (Stage 12 vs. Stage 4)
*Low-pass filtered across rolling multi-phase epochs ($\beta \in [0.6, 0.85]$) to eliminate single-phase noise (Invariant 10).*

| Objective / Expected Benefit (Stage 4) | Target Baseline Metric | Actual Realized Metric (Stage 12) | Delta / Variance | Measurement Horizon (`Immediate` \| `Deferred`) | Deferred Audit Due Date | Causal Factor (Stage 11/15) | Strategic Directive (Stage 18) |
|---|---|---|---|---|---|---|---|
| *<Metric 1>* | *<Target>* | *<Observed>* | *<Variance>* | `Immediate` | N/A | *<Root cause from audits>* | *<Maintain / Pivot / Retire>* |
| *<Metric 2>* | *<Target>* | *<Observed>* | *<Variance>* | `Deferred` | *<YYYY-MM-DD>* | *<Warmup / soak factor>* | *<Retain target; monitor>* |

---

## 4. Hypothesis Adjudication Register (Stage 3 Terminal Adjudication)
*All hypotheses must reach terminal state (Invariant 6). Maximum recurrence depth $d_{\max} = 2$ before mandatory collapse to VALIDATED ($BF_{10} \ge 10$) or REFUTED ($BF_{10} \le 0.1$) (Invariant 11).*

| Hypothesis ID | Statement | Recurrence Depth (0–2) | Bayes Factor ($BF_{10}$) | Empirical Test Evidence (Stage 10/12) | Terminal Disposition (`VALIDATED` \| `REFUTED` \| `REFINED`) | Strategic Impact / Graduation Target |
|---|---|---|---|---|---|---|
| `HYP-001` | *<Statement>* | 0 | 14.2 | *<Pytest / benchmark log ref>* | `VALIDATED` | *Graduated to Core Architecture Invariant* |
| `HYP-002` | *<Statement>* | 1 | 0.05 | *<Audit finding ref>* | `REFUTED` | *Formally retired with negative learning penalty* |
| `HYP-003` | *<Statement>* | 1 | 1.8 | *<Inconclusive evidence>* | `REFINED` | *Reformulated as HYP-003.2 for Phase N+1* |

---

## 5. Strategic Pivots & Lessons Learned Synthesis
- **Refined Problem Statement:** <How has our understanding of the core problem evolved through real execution?>
- **Updated Strategic Motivation:** <What new priorities, boundary conditions, or goals supersede the original spark/ideation?>
- **Retired Premises:** <What assumptions, capabilities, or dependencies are formally decommissioned based on negative evidence?>

---

## 6. Phase N+1 Spark Directives (Generational Handoff)
*(Omitted if disposition_type == "project_termination")*
- **Primary Catalyst for Phase N+1:** <What specific opportunity or gap initiates the next turn of the 18-stage wheel?>
- **Targeted Capabilities:** <What new capabilities or modules should the subsequent Project Charter authorize?>
- **Parent Refinement Linkage:** `parent_refinement: "IR-PROP-v<X.Y.Z>"` (ensures cross-generational traceability).
- **Inherited Hypotheses:** All `REFINED` hypotheses from Section 4 are automatically inherited into `Spark-Capture.vNext.md` (Invariant 15).

---

## 7. Administrative & Resource Decommissioning (Invariant 9)
- [ ] **Ephemeral Worktrees Pruned:** Temporary git worktrees from Stage 8 decommissioned; logs archived to `history/`.
- [ ] **Credentials & Sandboxes Revoked:** Temporary API session tokens, ephemeral model endpoints, and sandboxes released.
- [ ] **Cost Reconciliation:** Total compute and token expenditures reconciled against the Stage 4 Cost Baseline.

---

## 8. Governance Authorization
This Intent Refinement Proposal must be formally evaluated and approved via `approve-intent-refinement` (`FULL` Bayesian authority, `requires_human_approval: true`). Upon approval, this proposal closes the current phase baseline and initializes `Spark-Capture.vNext.md` (or concludes project archiving if `project_termination`).

