---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "9.1 Resource Management Plan"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-subsidiary-plan
inputs:
  - "Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
process: "Plan and formalize Resource Management Plan"
outputs:
  - "Resource-Management-Plan.md"
pmp_baseline: "PMP-BL-v1.0.0"
---

# Resource Management Plan — mxc

> **PMBOK 8 Process:** `9.1 Resource Management Plan` (Planning)  
> **Governance Policy:** `approve-subsidiary-plan` (foundation pack); rolls into `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Project-Charter.md](../Project-Charter.md), approved scope and schedule packs, [Resource Foundation Pack](resource-baseline/Resource-Foundation-Pack-Manifest.md)

## 1. Purpose & scope of this plan

Defines how **human and virtual resources** are identified, staffed, tooled, and controlled for Phase-1 product work **WBS 1.1.1–1.6.4**, using **78 WD** critical-path demand from the **approved schedule baseline**.

## 2. Resource baseline contents (Stage 7.C)

| Artifact | Location |
|---|---|
| Pillar overview & trace | [Resource-Pillar-Overview-and-Trace.md](resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md) |
| Role catalogue (skills + rates) | [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md) |
| Capacity estimates | [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md) |
| Tooling & assignment | [Resource-Tooling-and-Assignment-Register.md](resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md) |
| Team operating charter | [Resource-Team-Operating-Charter.md](resource-baseline/foundation/Resource-Team-Operating-Charter.md) |
| Utilization & control | [Resource-Utilization-and-Control-Protocol.md](resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md) |
| Domain checklist | [Resource-Domain-Checklist.md](resource-baseline/foundation/Resource-Domain-Checklist.md) |

**Pack manifest:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) — **v1.0.0**, **`pack_status: approved`** (7.C-8 complete 2026-11-10).

## 3. Resource standards

- **Roles:** **R-PLT**, **R-REL**, **R-SEC**, **R-SRE**, **R-QA**, **R-PM**, **R-ARC**, plus virtual **V-AGT** (no labor rate).
- **Units:** Schedule **WD** × **6 h** = planned hours; **EUR/h** ROM uses **market-conform contractor** rates only (**payroll loaded N/A** — no employer rate book).
- **WBS authority:** Primary role per story in role catalogue; owners remain per [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md).
- **Cost handoff:** ROM labor in capacity estimates aligns with approved **7.D** cost pack (**CAT-LAB** **€50,610**).

## 4. Approved resource baseline roll-up (2026-11-10)

| Element | Value |
|---|---|
| CP labor ROM | **€50,610** contractor market ↔ **CAT-LAB** |
| Roles | R-PLT, R-REL, R-SEC, R-SRE, R-QA, R-PM, R-ARC + **V-AGT** |
| Gate record | [approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json) |
| PMP next step | Register in [Project-Management-Plan.md](../Project-Management-Plan.md) §3.3 under **`approve-pmp`** |

## 5. Review & governance invariant

Integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). **Approved** resource baseline does not authorize hiring or contractor SOWs without Stage 8 and procurement gates.

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json).
