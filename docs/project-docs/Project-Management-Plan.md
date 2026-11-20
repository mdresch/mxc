---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan"
pmp_baseline: "PMP-BL-v1.0.0 (provenance unverified; not approved)"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
  - "management-plans/*.md"
process: "Integrate approved subsidiary management plans and establish authorized project baselines"
outputs:
  - "Project-Management-Plan.md"
status: "Draft — not ready for approval"
---

# Project Management Plan — MXC Hyper-V for ADPA / SIDPA

> **Status:** Draft only. The Charter is approved; this PMP and its subsidiary plans are not. No PMP baseline or execution baselines are approved by this document.
> **Baseline label in downstream documents:** `PMP-BL-v1.0.0` is referenced by existing artifacts, but this repository currently has no canonical `approve-pmp` approval record establishing it as an approved baseline.

## 1. Authorization and planning status

The [Project Charter](Project-Charter.md) was approved by the Steering Committee on 2026-10-30. It authorizes project planning within its stated scope and USD 25,000 Project Manager spending authority. It does not approve this PMP or any subsidiary plan.

The subsidiary plans below are drafts for review. Seven can be prepared from the available charter inputs; the Schedule Management Plan and Cost Management Plan are explicitly not yet buildable under the Charter's evidence requirements.

| Subsidiary plan | Current status |
|---|---|
| Scope Management Plan | Draft; Scope Foundation Pack pending review and initiating-input reconciliation |
| Quality Management Plan | Draft; requirements and test-owner assignments remain incomplete |
| Resource Management Plan | Draft; no capacity or resource allocation is approved |
| Communications Management Plan | Draft; committee membership and cadence remain open |
| Risk Management Plan | Draft; no probability/impact scale or cadence is approved |
| Procurement Management Plan | Draft; no procurement need or commitment is identified |
| Stakeholder Engagement Plan | Draft; individual committee membership is not recorded |
| Schedule Management Plan | Not yet buildable; actual duration data and approved scope/WBS are prerequisites |
| Cost Management Plan | Not yet buildable; Resource Allocation and Procurement outputs are prerequisites |

## 2. Baselines

- **Scope baseline:** Not approved. The Scope Foundation Pack and its artifacts remain drafts/pending.
- **Schedule baseline:** Not established. No dates or duration estimates are authorized.
- **Cost baseline:** Not established. The USD 25,000 amount is an approval threshold, not a total budget.
- **Benefits baseline:** Operational targets are recorded in the Benefits Statement, which remains draft. The paused-RAM target conflicts with upstream documents and the surge measurement window remains open.

## 3. Governance and decisions

Use the applicable human governance gate for each baseline. Approval of the Charter is not approval of this PMP. The Steering Committee provides independent approval for this PMP and commitments above USD 25,000; individual member names and the standing approval process remain to be recorded.

Preserve decision evidence and identify the artifact revision reviewed. Downstream references to `PMP-BL-v1.0.0` must not be interpreted as approval: resolve their provenance before roll-up or approval.

## 4. Dependencies and open planning inputs

1. Approve the Benefits Statement or otherwise record its authorized disposition.
2. Resolve and record the RAM target and surge measurement window before baselining affected measures.
3. Complete and review the Scope Foundation Pack; preserve its pending state until all prerequisites are met.
4. Record resource allocations and any procurement outputs before preparing cost planning.
5. Gather actual duration evidence after completed work before preparing schedule planning.
6. Name Steering Committee members and confirm the committee approval process.

Track open items in the [Assumption Log](Assumption-Log.md). No subsidiary plan or baseline is approved merely because a file exists or is linked here.

## 5. Governance and approval

This PMP is the Stage 7 document and requires independent Steering Committee review and approval under `approve-pmp` (`FULL` authority, `requires_human_approval: true`) before it becomes the integrated Project Management Plan or establishes baselines. Stage 6 requirement packs 001–006 are already approved. The subsidiary plans are drafts for review pending `approve-subsidiary-plan` and `approve-pmp`. This file does not authorize Stage 8 or Stage 9.
