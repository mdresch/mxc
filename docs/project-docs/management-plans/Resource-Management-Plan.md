---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "9.1 Resource Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Benefits-Statement.md"
process: "Identify resource roles, authority, constraints, and allocation evidence"
outputs:
  - "Resource-Management-Plan.md"
status: "Draft — pending review and approve-pmp"
---

# Resource Management Plan — MXC Hyper-V for ADPA / SIDPA

> **Status:** Draft for review. This plan identifies known roles and resource constraints; it does not allocate unconfirmed capacity. `approve-subsidiary-plan` has not been run.

## Roles and authority

| Role | Assigned person / record |
|---|---|
| Project Sponsor and Project Manager | Menno Drescher (dual role) |
| Operational Benefit Owner | Menno Drescher |
| Steering Committee | Sponsor, CFO, Finance Controller, IT Engineering, IT Analysis, HR, Learning and Development; individual members not named |
| Technical/test owners | Not assigned |

Because the sponsor and project manager are the same person, the Steering Committee provides independent approval for the Charter and expenditures above USD 25,000. Menno does not approve these alone.

## Resource planning and constraints

No staffing levels, availability, host count, skills allocation, or total resource budget are established. Record each resource request with role/skill, purpose, expected timing, availability evidence, and approval before treating it as committed. Do not infer named technical, operations, security, or product owners from stakeholder categories.

The technical workload has standing resource requirements: paused guests retain RAM and image disks even when CPU/GPU use is zero. The selected paused RAM target is under 700 MB per guest, but upstream documents still record about 1.0–1.2 GB. Do not use either figure for capacity planning until reconciled and measured. Production-image readiness and the pool surge window remain dependencies.

## Acquisition, assignment, and escalation

The Project Manager coordinates requests and tracks assignments. Any expenditure exceeding USD 25,000 requires Steering Committee approval before commitment. The Charter does not state additional authority limits, charge rates, allocation percentages, or escalation timelines.

## Approval and open dependencies

This document is a draft, not a resource allocation baseline. Resource availability and procurement outputs are prerequisites to a buildable Cost Management Plan. Approval is required under `approve-pmp`.
