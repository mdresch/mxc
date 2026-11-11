---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "11.1 Plan Risk Management"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-pmp
pmp_baseline: "PMP-BL-v1.0.0"
inputs:
  - "Project-Charter.md"
  - "Business-Case.md"
  - "schedule-baseline/foundation/Schedule-Reserve-Register.md"
  - "cost-baseline/foundation/Cost-Estimates-by-Category.md"
process: "Plan and formalize Risk Management Plan"
outputs:
  - "Risk-Management-Plan.md"
---

# Risk Management Plan — mxc

> **PMBOK 8 Process:** `11.1 Plan Risk Management` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Business-Case.md](../Business-Case.md), approved schedule reserves, cost contingency envelope

## 1. Purpose & scope

Defines risk **identification**, **analysis**, **response**, and **monitoring** for Phase-1 **mxc** (WBS **1.1.1–1.6.4**) under **`PMP-BL-v1.0.0`**. Schedule **management reserve** rows (**SCH-RSV-***) and cost **CAT-CONT** are the funded response path for identified uncertainties.

## 2. Methodology

| Step | Practice |
|---|---|
| Identify | Pillar epics, domain checklists, open questions (Q-SCH-*, Q-RES-*, Q-SCOPE-*) |
| Analyze | Qualitative **H/M/L** impact × likelihood; link to TP-01…TP-06 |
| Respond | Avoid / mitigate / transfer / accept; draw reserves only with trigger evidence |
| Monitor | Project status register; adaptation plan when thresholds breach |
| Escalate | Material product or baseline risk → sponsor via communications plan |

**Quantitative analysis:** Not required for Phase-1 ROM; use WD ranges and cost low/likely/high from approved cost pack.

## 3. Phase-1 risk register

| ID | Risk | Pillar | L×I | Response strategy | Trigger / indicator | Reserve / owner |
|---|---|---|---|---|---|---|
| RSK-01 | Guest isolation regression | TP-01 | H×M | Mitigate — sandbox + contract tests | Failed isolation harness | R-PLT; **SCH-RSV-MGT** if systemic |
| RSK-02 | Ingress wake latency SLO miss | TP-02 | H×M | Mitigate — bench + RSV buffer | AC-01.1 breach in harness | **SCH-RSV-001** |
| RSK-03 | Image/catalog drift | TP-03 | M×M | Mitigate — audit scripts | `audit_production_image` fail | **SCH-RSV-002** |
| RSK-04 | Paused footprint not achieved | TP-04 | M×M | Mitigate — formulated metrics | RAM/CPU gate fail | Accept + story iteration |
| RSK-05 | Session sterility leak | TP-05 | H×M | Mitigate — differencing + pool release | Parent VHDX hash change | **SCH-RSV-003**; R-SEC |
| RSK-06 | Pool watermark instability | TP-06 | M×M | Mitigate — surge policy tests | Watermark breach in test | **SCH-RSV-004** |
| RSK-07 | Schedule optimism (no velocity history) | Cross | M×H | Accept + reserve | Slip > 10% CP WD | **Q-SCH-001**; PM |
| RSK-08 | Contractor mix undefined | Resource | M×M | Transfer / mitigate — SOW | External role engaged | **Q-RES-003**; Procurement |
| RSK-09 | Tooling subscription creep | Cost | L×M | Mitigate — variance protocol | **CAT-TOOL** ≠ €71/mo | PM; cost manifest |
| RSK-10 | Agentic parallel lane collision | Execution | M×M | Mitigate — Tier A/B policy | Double claim same WBS | PM; story queue |
| RSK-11 | PMP not locked before story flood | Governance | H×L | Avoid — **`approve-pmp`** | Stage 8 without PMP gate | **Mitigated (2026-11-10)** — PMP approved |

## 4. Contingency & reserves linkage

| Mechanism | Planning envelope | Authority |
|---|---|---|
| **SCH-RSV-001…004, MGT** | WD ranges in [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) | PM + sponsor on trigger |
| **CAT-CONT** | **€18k – €28k** if all reserves burn | Finance view via cost pack |
| **CAT-INFRA** | €0 – €2k placeholder | Sponsor on infra tier change |

Drawing reserve **must** update story queue, registers, and optionally adaptation plan — not silent scope expansion.

## 5. Roles

| Role | Risk duty |
|---|---|
| **PM** | Register owner, reserve trigger coordinator |
| **R-PLT / R-SRE** | Technical risk identification per pillar |
| **R-SEC** | Security-specific risks and acceptances |
| **Sponsor** | Accept residual risks; fund CONT draw |

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | **§2.11.1**, **§3.7** |
| Living updates | Risk IDs appended in this plan or adaptation; version with PMP bump |
| Lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

Risk planning is verified under **`approve-pmp`**. Open questions in subsidiary manifests remain **accepted risks** until closed.

**Status:** **Approved (2026-11-10)** — register operational for Phase 1; rolled into PMP.
