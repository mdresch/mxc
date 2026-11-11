---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/*.md"
process: "Integrate subsidiary management plans, establish baselines, define governance gates"
outputs:
  - "Project-Management-Plan.md"
---

# Project Management Plan (PMP) — SIDPA Project

**Status:** Scaffold. `approve-pmp` has not been run. Packs 001–006 cite `PMP-BL-v1.0.0`, and that citation is not a locked Stage 7 baseline.

> **PMBOK 8 Process:** `4.2 Develop Project Management Plan` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 7 (Planning: Integrated PMP & Baselines)`  
> **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Inputs:** Project-Charter.md, Subsidiary Management Plans  
> **Process:** Integrate subsidiary management plans, establish baselines, define governance gates  
> **Outputs:** Project-Management-Plan.md

## 1. Executive Summary & Baselines
- **Project Title:** SIDPA Project
- **Baseline ID:** `PMP-BL-v1.0.0`
- **Scope Baseline:** Approved scope boundary traced to Project Charter objectives.
- **Schedule Baseline / Progressive Elaboration:** Milestones established; duration detailed progressively from empirical evidence.
- **Cost Baseline / Progressive Elaboration:** Investment limits from Business Case; detailed cost tracked as resources are committed.

## 2. Integrated Subsidiary Management Plans

### 2.5.1 Scope Management Plan
**Document Link:** [management-plans/Scope-Management-Plan.md](management-plans/Scope-Management-Plan.md)
- **Summary:** Formulated Scope Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.6.1 Schedule Management Plan
**Document Link:** [management-plans/Schedule-Management-Plan.md](management-plans/Schedule-Management-Plan.md)
- **Summary:** Formulated Schedule Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.7.1 Cost Management Plan
**Document Link:** [management-plans/Cost-Management-Plan.md](management-plans/Cost-Management-Plan.md)
- **Summary:** Formulated Cost Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.8.1 Quality Management Plan
**Document Link:** [management-plans/Quality-Management-Plan.md](management-plans/Quality-Management-Plan.md)
- **Summary:** Formulated Quality Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.9.1 Resource Management Plan
**Document Link:** [management-plans/Resource-Management-Plan.md](management-plans/Resource-Management-Plan.md)
- **Summary:** Formulated Resource Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.10.1 Communications Management Plan
**Document Link:** [management-plans/Communications-Management-Plan.md](management-plans/Communications-Management-Plan.md)
- **Summary:** Formulated Communications Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.11.1 Risk Management Plan
**Document Link:** [management-plans/Risk-Management-Plan.md](management-plans/Risk-Management-Plan.md)
- **Summary:** Formulated Risk Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.12.1 Procurement Management Plan
**Document Link:** [management-plans/Procurement-Management-Plan.md](management-plans/Procurement-Management-Plan.md)
- **Summary:** Formulated Procurement Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

### 2.13.2 Stakeholder Engagement Plan
**Document Link:** [management-plans/Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md)
- **Summary:** Formulated Stakeholder Engagement Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....

## 3. Feedback Loop from Adaptation
When an **Adaptation Plan** (Stage 17) is approved, this PMP and its subsidiary plans are updated with tailored operational changes evaluated through the Governance Change Impact Matrix, which in turn trigger refined ADRs, BRDs, FDDs, and Stories for the next cycle. Prior baselines are archived to `management-plans/history/{baseline_id}/`.

## 4. Governance Authorization
Stage 6 requirement packs 001–006 are already approved. This PMP is the Stage 7 document and is not approved. `approve-pmp` (`FULL` authority, `requires_human_approval: true`) has not been run. Invariant 1 in `docs/chain-coverage.md` puts those requirements before this baseline, which is the order already used. The nine subsidiary plans are still scaffolds titled "SIDPA Project". `approve-subsidiary-plan` has not been run. This file does not authorize Stage 8 or Stage 9.
