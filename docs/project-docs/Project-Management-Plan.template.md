---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Project)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
  - "Subsidiary management plans (Scope, Risk, Quality, etc.)"
process: "Integrate subsidiary management plans, establish baselines, define governance gates"
outputs:
  - "Project-Management-Plan.md"
---

# Project Management Plan (PMP)

> **PMBOK 8 Process:** `4.2 Develop Project Management Plan` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 6 (Project)`  
> **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Inputs:** Project-Charter.md, Subsidiary management plans (Scope, Risk, Quality, etc.)  
> **Process:** Integrate subsidiary management plans, establish baselines, define governance gates  
> **Outputs:** Project-Management-Plan.md


**Source:** [Project-Charter.md](Project-Charter.md)
**Governance Policy:** `approve-pmp`

**This is the integrated Project Management Plan, formalized after the Project Charter is approved and before technical specifications (ADR, BRD, FDD, User Stories) are drafted.**

## 1. Executive Summary & Baselines
- **Scope Baseline:** Approved scope boundary traced to Charter objectives.
- **Schedule Baseline / Progressive Elaboration:** Milestones established; duration detailed progressively from empirical evidence.
- **Cost Baseline / Progressive Elaboration:** Investment limits from Business Case; detailed cost tracked as resources are committed.
- **Baseline ID:** `PMP-BL-v1.0.0` (Invariant 6)

## 2. Integrated Subsidiary Management Plans
- **Scope Management Plan:** How requirements and scope changes are evaluated and controlled.
- **Requirements Management Plan:** Traceability chain from Charter to ADR/BRD/FDD/Stories.
- **Risk Management Plan:** Risk register, probability/impact scoring, and mitigation protocols.
- **Quality Management Plan:** Contract-test criteria, zero-drift verification, and regression prevention rules.
- **Resource Management Plan:** Roles, responsibilities, and agent authority tiers.
- **Communications Management Plan:** Project transparency, PR reviews, and audit log cadence.
- **Stakeholder Engagement Plan:** Human approval gates and escalation pathways.

## 3. Feedback Loop from Adaptation
When an **Adaptation Plan** (Stage 17) is approved, this PMP and its subsidiary plans are updated with tailored operational changes, which in turn trigger refined ADRs, BRDs, FDDs, and Stories for the next cycle.

## What this is not yet
This document integrates governance and operational plans. It does NOT contain code architecture or solution logic—those belong in ADRs, BRDs, and FDDs, which are drafted only after this PMP is approved.
