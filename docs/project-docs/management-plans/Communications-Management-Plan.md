---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "10.1 Plan Communications Management"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-pmp
pmp_baseline: "PMP-BL-v1.0.0"
inputs:
  - "Project-Charter.md"
  - "Stakeholder-Register.md"
  - "registers/Project-Status-Register.md"
process: "Plan and formalize Communications Management Plan"
outputs:
  - "Communications-Management-Plan.md"
---

# Communications Management Plan — mxc

> **PMBOK 8 Process:** `10.1 Plan Communications Management` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Stakeholder-Register.md](../Stakeholder-Register.md), [Project-Status-Register.md](../../registers/Project-Status-Register.md)

## 1. Purpose & scope

Defines **what** project information is shared, **with whom**, **how often**, and **through which channels** during Phase-1 planning and (when authorized) execution of **mxc** under **`PMP-BL-v1.0.0`**.

## 2. Communication requirements

| Need | Audience | Constraint |
|---|---|---|
| Baseline truth | Sponsor, PM, leads | Registers and manifests are authoritative over chat summaries |
| Integration queue | Engineering | [Implementation-Story-Queue.md](../../registers/Implementation-Story-Queue.md) + Tier A/B policy |
| Governance decisions | PM, sponsor | Gate JSON in `docs/project-docs/gates/` |
| Agent sessions | PM (optional) | Transcripts are **not** approval evidence unless cited in registers |
| External consumers | SecOps / SRE (future) | No public comms until product validation stories complete |

## 3. Distribution matrix (Phase 1)

| Information | Producer | Audience | Channel | Cadence |
|---|---|---|---|---|
| Orientation snapshot | PM | Sponsor, leads | [Project-Status-Register.md](../../registers/Project-Status-Register.md) | Update at natural pauses; after epic recap |
| Story claim / lane status | PM / leads | Integrators | Implementation story queue | On claim or release |
| Subsidiary plan approval | PM | Sponsor | PMP §3 + gate adjudication JSON | On gate completion |
| PR / code review | Authors | R-QA, peers | GitHub PR (Basic plan) | Per change |
| Cost / subscription actuals | Sponsor | PM | Invoice + cost variance protocol | Monthly (**CAT-TOOL** €71/mo plan) |
| Reserve consumption | PM | Sponsor | Schedule + cost reserve registers | When **SCH-RSV-*** triggered |
| Stage 8 authorization | Sponsor | All SH-* | Stage 8 notice (when issued) | Once per phase entry |

## 4. Escalation & response times

| Trigger | Escalate to | Target response | Record |
|---|---|---|---|
| Scope creep / unscoped merge | PM → sponsor | 1 business day | Status register + scope monitor |
| Integration story blocked > 2 days | PM | Same day triage | Story queue |
| Security defect on guest path | R-SEC → PM | Immediate stop-work on affected story | Adaptation / risk register |
| Contractor SOW variance | Procurement → sponsor | Before next invoice | Procurement plan §5 |

## 5. Tools (communications)

| Tool | Use | Cost category |
|---|---|---|
| **GitHub** | PRs, issues, checks | **CAT-TOOL** |
| **Cursor / agents** | Implementation assist | **CAT-TOOL** |
| **Markdown registers** | Durable project record | In-repo |
| Email / calendar | Sponsor sync | Sponsor overhead (not in labor baseline) |

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | **§2.10.1**, **§3.6** |
| Stakeholder cross-ref | [Stakeholder-Engagement-Plan.md](Stakeholder-Engagement-Plan.md) |
| Lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

Communications planning is verified under **`approve-pmp`**. This plan does not mandate a specific chat product; it mandates **register-first** truth.

**Status:** **Approved (2026-11-10)** — rolled into PMP.
