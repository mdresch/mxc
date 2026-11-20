---
artifact_id: schedule-foundation-pack-manifest
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-pmp
version: "1.0.0"
owner_role: Project Manager
depends_on:
  - scope-management
pack_status: approved
---

# Schedule Foundation Pack — Manifest (PMP-BL-v1.0.0)

Project: **MXC Hyper-V for ADPA / SIDPA**. Stage 6.B establishes the Schedule Baseline, defining the WBS activity network, critical path, PERT forecast, and asynchronous wave calendar model.

## Stage 6.B process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|:---:|
| 6.B-0 | Scope plan and WBS reconciliation | [Scope-WBS-Dictionary.md](../scope-baseline/foundation/Scope-WBS-Dictionary.md) WBS 1.0–8.0 mapped | **approved** |
| 6.B-0P | [Schedule-Pillar-Overview-and-Trace.md](foundation/Schedule-Pillar-Overview-and-Trace.md) | 6 Topic Pillars (TP-01 to TP-06) traced to Milestones M1–M5 | **approved** |
| 6.B-1 | [Schedule-Basis-of-Estimates.md](foundation/Schedule-Basis-of-Estimates.md) | Agent turns, runtime, and review latency basis documented | **approved** |
| 6.B-2 | [Schedule-Network-Phase1.md](foundation/Schedule-Network-Phase1.md) | Mermaid dependency network and critical path ($31.0\text{h}$) defined | **approved** |
| 6.B-2A | [Schedule-Activity-List-Phase1.md](foundation/Schedule-Activity-List-Phase1.md) | Activities ACT-01 to ACT-19 decomposed with agent contracts | **approved** |
| 6.B-2B | [Schedule-Gantt-Phase1.md](foundation/Schedule-Gantt-Phase1.md) | Asynchronous wave schedule model with float and milestones | **approved** |
| 6.B-3 | [Schedule-Reserve-Register.md](foundation/Schedule-Reserve-Register.md) | Contingency ($8.5\text{h}$) and Management ($6.5\text{h}$) reserves allocated | **approved** |
| 6.B-4 | [Schedule-Baseline-WBS-Forecast.md](foundation/Schedule-Baseline-WBS-Forecast.md) | 3-point PERT estimates and turn budgets per work package | **approved** |
| 6.B-5 | [Schedule-Domain-Checklist.md](foundation/Schedule-Domain-Checklist.md) | PMBOK 8 Schedule outcomes verified PASS | **approved** |
| 6.B-6 | Pack roll-up | Artifacts reviewed; registry complete and audited | **approved** |
| 6.B-7 | Schedule plan approval | Approved under `approve-pmp` by Menno Drescher | **approved** |

---

## Artifact registry

| Artifact | Substage | Version | Review status | Reviewer / date | SHA-256 after approval |
|---|:---:|:---:|:---:|:---:|---|
| [Schedule-Pillar-Overview-and-Trace.md](foundation/Schedule-Pillar-Overview-and-Trace.md) | 6.B-0P | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `B5BC25618342D47DD13EB7C00B572ECA60F26DA4B72D84563A937ECF7CEDAE2E` |
| [Schedule-Basis-of-Estimates.md](foundation/Schedule-Basis-of-Estimates.md) | 6.B-1 | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `67359CE646EFDDA0BFD47E3ADB7541DAC246845C8AB6968C67155FD01426ABF2` |
| [Schedule-Network-Phase1.md](foundation/Schedule-Network-Phase1.md) | 6.B-2 | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `8F232D26672A4E97DE193E3908935A81ECC1A843A53E062EEC2353A9A7C5E216` |
| [Schedule-Activity-List-Phase1.md](foundation/Schedule-Activity-List-Phase1.md) | 6.B-2A | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `683B40B48F26C0301AC8F8B738A87D2A8237508FFCDB36BB858EF52DEC099944` |
| [Schedule-Gantt-Phase1.md](foundation/Schedule-Gantt-Phase1.md) | 6.B-2B | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `0754A5F8D8D279152A2B95A2BBE175D6ED0A65E9114A6FA37D52BAF2C3512961` |
| [Schedule-Reserve-Register.md](foundation/Schedule-Reserve-Register.md) | 6.B-3 | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `A02F4A05ADA653AE9704356547E2DBFAB0AC9D1AD5B4D9BC489EA96DD661FC7A` |
| [Schedule-Baseline-WBS-Forecast.md](foundation/Schedule-Baseline-WBS-Forecast.md) | 6.B-4 | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `CF052B53E31D34ADB8A325EE97C9B41BC3265BFF812FD33100878E326704D8DF` |
| [Schedule-Domain-Checklist.md](foundation/Schedule-Domain-Checklist.md) | 6.B-5 | 1.0.0 | approved | Menno Drescher / 2026-11-20 | `A11BADAF1F28038C0D8B9EB86A691C5E77E9BC345AB33F20F1BAEB55FA2F3CE8` |

---

## Roll-up and approval record

All Stage 6.B foundation artifacts are formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. This establishes the **Schedule Baseline** for `PMP-BL-v1.0.0`.
