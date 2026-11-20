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
process: "Define how project scope is developed, validated, and controlled"
outputs:
  - "Scope-Management-Plan.md"
status: "Draft — pending review and approve-pmp"
---

# Scope Management Plan — MXC Hyper-V for ADPA / SIDPA

> **Status:** Draft for review. This plan does not establish an approved scope baseline or authorize implementation. `approve-subsidiary-plan` has not been run.

## Purpose and scope approach

Use the approved [Project Charter](../Project-Charter.md) as the current authorization boundary. Decompose the charter's in-scope outcomes into deliverables and work packages only when each can be traced to an approved requirement and measurable acceptance evidence. The existing [Scope Foundation Pack](scope-baseline/Scope-Foundation-Pack-Manifest.md) remains pending; its draft artifacts are not baselines.

Scope planning covers the six architecture pillars and integrated acceptance identified in the project materials: isolation, ingress, production image supply, paused footprint, session sterility, and pool/wake hygiene. The exclusions in the Charter remain excluded unless formally changed.

## Requirements, scope statement, and WBS

- Maintain traceability from each charter objective and benefit to its approved BRD, architecture decision, work package, and acceptance evidence.
- The scope statement and WBS remain proposals until the Benefits Statement and baseline provenance issues in the Scope Foundation Pack are resolved and human review is recorded.
- Do not add delivery dates, duration estimates, cost estimates, host counts, or resource commitments to scope artifacts.
- Keep each deliverable independently verifiable. Do not combine path-based pool routing with listener-port image selection; treat them as separate checks.

## Scope validation and acceptance

Validate a deliverable against the exact approved requirement and its test evidence. Record the criterion, source revision, test environment, result, reviewer, date, and governance disposition. The Project Manager coordinates the evidence; acceptance authority and named technical reviewers remain unassigned.

Unresolved thresholds are not pass/fail criteria until reconciled: the paused-RAM target conflicts between the Charter/Benefits Statement and Ideation/Business Case, and the surge threshold lacks a measurement window. Production-image acceptance depends on the bake being complete.

## Scope change and control

For each proposed change, record rationale, source, affected objectives/requirements/WBS, and impacts on benefits, schedule, cost, quality, risk, resources, security, and stakeholders. No change becomes part of the baseline until the applicable human governance gate approves it. Escalate spending above USD 25,000 to the Steering Committee for approval before commitment. The Charter does not establish other scope-change thresholds or standing meeting cadence.

## Approval and open dependencies

This draft requires review and approval through `approve-pmp` before it is treated as an approved subsidiary plan. The Scope Foundation Pack remains pending while its initiating-input and PMP-baseline provenance questions are open. See the [Assumption Log](../Assumption-Log.md).
