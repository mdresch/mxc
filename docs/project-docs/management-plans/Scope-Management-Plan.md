---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.1 Scope Management Plan"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-subsidiary-plan
inputs:
  - "Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
process: "Plan and formalize Scope Management Plan"
outputs:
  - "Scope-Management-Plan.md"
pmp_baseline: "PMP-BL-v1.0.0"
---

# Scope Management Plan — mxc

> **PMBOK 8 Process:** `5.1 Scope Management Plan` (Planning)  
> **Governance Policy:** `approve-subsidiary-plan` (foundation pack); rolls into `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Project-Charter.md](../Project-Charter.md), [Scope Foundation Pack](scope-baseline/Scope-Foundation-Pack-Manifest.md)

## 1. Purpose & scope of this plan

This plan defines how the **mxc** JIT Hyper-V product scope—decomposed as WBS **1.1–1.6** from accepted **ADR-001–006** and approved **BRD/FDD/epic 001–006**—is documented, validated, controlled, and rolled into the [Project Management Plan](../Project-Management-Plan.md) at baseline **`PMP-BL-v1.0.0`**.

## 2. Scope baseline contents

The authoritative scope baseline for planning is the **Scope foundation pack** (Stage 7.A):

| Artifact | Location |
|---|---|
| Pillar overview & trace | [Scope-Pillar-Overview-and-Trace.md](scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md) |
| Project scope statement | [Scope-Project-Scope-Statement.md](scope-baseline/foundation/Scope-Project-Scope-Statement.md) |
| WBS dictionary | [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) |
| Monitor & control scope | [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md) |
| Validate scope | [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md) |
| Domain checklist | [Scope-Domain-Checklist.md](scope-baseline/foundation/Scope-Domain-Checklist.md) |

**Pack manifest:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) — **v1.2.0**, **`pack_status: approved`** (7.A-7 complete 2026-11-10).

Roll-up includes WBS **1.0**, pillars **1.1–1.6**, and **17** user-story packages **1.N.S** with SHA-256 fingerprints in the manifest registry.

## 3. Scope definition & WBS

- **Product scope:** WBS **1.0** — six topic pillars (**TP-01–TP-06**) mapped to implementation epics and suite architecture under `docs/hyperv/architecture/`.
- **Project scope:** WBS **2.x** — SIDPA governance, subsidiary plans, and quality gates.
- **Decomposition standard:** Pillar **`1.N`**, user story **`1.N.S`** (17 stories)—see WBS dictionary and story index.

## 4. Validate scope

Specification validation is satisfied by governance gates on ADR/BRD/FDD/epic packs. Product validation requires **`implement-story`**, contract tests, and future **`approve-audit-record`** entries. See [Scope-Validate-Scope.md](scope-baseline/foundation/Scope-Validate-Scope.md).

## 5. Control scope

Changes flow through the paired governance pipeline (`classify-diff-type` → `escalate-diff-response` / adaptation plan) and artifact-specific `approve-*` gates. Unscoped implementation is logged in the project status register. See [Scope-Monitor-Control-Scope.md](scope-baseline/foundation/Scope-Monitor-Control-Scope.md).

## 6. Review & governance invariant

This subsidiary plan integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Foundation pack approval uses **`approve-subsidiary-plan`**; integrated PMP lock uses **`approve-pmp`**. Creating or filling this plan does not authorize execution (**Stage 8** notice still required).

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json).

**PMP roll-up:** Integrated into [Project-Management-Plan.md](../Project-Management-Plan.md) §3.1 **2026-11-10** (integrated **`approve-pmp`** lock **2026-11-10**).
