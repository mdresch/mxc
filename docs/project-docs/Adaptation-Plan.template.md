---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Monitoring & Controlling / Adaptive Closing"
pmbok_process: "4.6 Perform Integrated Change Control & Tailoring"
lifecycle_stage: "Stage 17 (Adaptation)"
governance_policy: "approve-adaptation-plan"
inputs:
  - "Stage 16 Governance Amendments (ADR Diffs)"
  - "Audit-Register.md findings"
process: "Operationalize governance changes into behavioral/skill updates and tailor management plan updates"
outputs:
  - "Adaptation-Plan.md"
  - "Updated Project Management Plan"
---

# Adaptation Plan

> **PMBOK 8 Process:** `4.6 Perform Integrated Change Control & Tailoring` (Monitoring & Controlling / Adaptive Closing)  
> **Governance Policy:** `approve-adaptation-plan` | **Lifecycle Stage:** `Stage 17 (Adaptation)`  
> **Inputs:** Stage 16 Governance Amendments (ADR Diffs), Audit-Register.md findings  
> **Process:** Operationalize governance changes into behavioral/skill updates and tailor management plan updates  
> **Outputs:** Adaptation-Plan.md, Updated Project Management Plan


**Source:** [Governance Change Log / ADR Diff]
**Governance Policy:** `approve-adaptation-plan`

## Triggering Governance Change
<Reference the specific validated ADR/BRD amendment, supersession, or policy update from Stage 16 that necessitates behavioral or process adaptation.>

## Scope of Behavioral / Tooling Adaptation
- **Workflow / Process Adjustments:** <What steps in the engineering, review, or operational workflow are modified?>
- **Agent Skill / Tooling Updates:** <What agent skills, hooks, or system prompts require revision to enforce the updated governance?>
- **Environmental / Configuration Changes:** <Any CI/CD, linter, or sandbox environment modifications.>

## Governance Change Impact Matrix
Every adaptation must formally assess and quantify the impact of accepted Stage 16 governance amendments across the 9 subsidiary management plans before selective re-orchestration:

| Amendment / Change | Scope (5.1) | Schedule (6.1) | Cost (7.1) | Quality (8.1) | Resource (9.1) | Comms (10.1) | Risk (11.1) | Procurement (12.1) | Stakeholder (13.2) |
|---|---|---|---|---|---|---|---|---|---|
| `<Amendment ID/Title>` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` | `None/Low/Med/High` |

## Tailored Subsidiary Management Plan Updates (Feeding back to PMP)
Identify which subsidiary management plans require updates as a direct result of this adaptation:
- [ ] **Scope Management Plan:** <Updates to scope boundaries or change control>
- [ ] **Schedule Management Plan:** <Adjusted timeline or duration baselines>
- [ ] **Cost Management Plan:** <Revised budget, investment limits, or reserve allocations>
- [ ] **Quality Management Plan:** <New contract test requirements or verification checks>
- [ ] **Resource Management Plan:** <Updated agent skill definitions, prompts, or authority limits>
- [ ] **Communications Management Plan:** <Modified reporting, audit, or notification rules>
- [ ] **Risk Management Plan:** <New risks, altered severity, or revised mitigation strategies>
- [ ] **Procurement Management Plan:** <Supplier, vendor, or external package changes>
- [ ] **Stakeholder Engagement Plan:** <Revised approval gates or escalation matrices>

*Any checked plan triggers selective execution via `python scripts/orchestrate_pmbok.py --mode adapt --adaptation-plan docs/project-docs/Adaptation-Plan.md`. Prior baselines are archived to `management-plans/history/{baseline_id}/`.*

## Rollback & Recovery Pathway
If post-adaptation execution reveals regressions or operational failure (detected via ADR-005 `compare_decision_results()`), atomic rollback is triggered:
1. Orchestrator restores the previous approved baseline (`PMP-BL-vX.Y.Z`) from `management-plans/history/`.
2. Emits negative reward (-1.5) to `escalate-diff-response` for the episode.
3. Restores verified operational stability without history corruption (Invariant 7).

## Verification & Rollout Gates
<Measurable criteria confirming the adaptation is successfully operating in practice without causing regressions.>

## What this is not yet
This is Stage 17 (Adaptation). It executes the operational and behavioral changes required by an already-approved Stage 16 Governance Change. Do not redefine core strategic intent here -- that belongs in Stage 18 Intent Refinement.
