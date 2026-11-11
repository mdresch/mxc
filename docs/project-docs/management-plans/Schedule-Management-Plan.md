---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "6.1 Schedule Management Plan"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-subsidiary-plan
inputs:
  - "Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
process: "Plan and formalize Schedule Management Plan"
outputs:
  - "Schedule-Management-Plan.md"
pmp_baseline: "PMP-BL-v1.0.0"
---

# Schedule Management Plan — mxc

> **PMBOK 8 Process:** `6.1 Schedule Management Plan` (Planning)  
> **Governance Policy:** `approve-subsidiary-plan` (foundation pack); rolls into `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Project-Charter.md](../Project-Charter.md), [Approved Scope Pack](scope-baseline/Scope-Foundation-Pack-Manifest.md), [Schedule Foundation Pack](schedule-baseline/Schedule-Foundation-Pack-Manifest.md)

## 1. Purpose & scope of this plan

This plan defines how **mxc** Phase-1 **product implementation** schedule—traced to WBS **1.1.1–1.6.4** (17 story packages) from the **approved scope baseline**—is estimated, sequenced, reserved, and controlled before roll-up into the [Project Management Plan](../Project-Management-Plan.md) at **`PMP-BL-v1.0.0`**.

## 2. Schedule baseline contents (Stage 7.B)

| Artifact | Location |
|---|---|
| Pillar overview & trace | [Schedule-Pillar-Overview-and-Trace.md](schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md) |
| Basis of estimates | [Schedule-Basis-of-Estimates.md](schedule-baseline/foundation/Schedule-Basis-of-Estimates.md) |
| Network (Phase 1) | [Schedule-Network-Phase1.md](schedule-baseline/foundation/Schedule-Network-Phase1.md) |
| Activity list (Phase 1) | [Schedule-Activity-List-Phase1.md](schedule-baseline/foundation/Schedule-Activity-List-Phase1.md) |
| Gantt model (Phase 1) | [Schedule-Gantt-Phase1.md](schedule-baseline/foundation/Schedule-Gantt-Phase1.md) |
| Reserve register | [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) |
| WBS duration forecast | [Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md) |
| Domain checklist | [Schedule-Domain-Checklist.md](schedule-baseline/foundation/Schedule-Domain-Checklist.md) |

**Pack manifest:** [Schedule-Foundation-Pack-Manifest.md](schedule-baseline/Schedule-Foundation-Pack-Manifest.md) — **v1.1.0**, **`pack_status: approved`** (7.B-7 complete 2026-11-10).

## 3. Scheduling standards

- **WBS authority:** [Scope-WBS-Dictionary.md](scope-baseline/foundation/Scope-WBS-Dictionary.md) — activity IDs equal story WBS IDs.
- **Units:** Working days (WD) of **human developer / engineer effort** (6 h focused time per WD); 5-day week. Ranges are analogous until **human** actuals exist.
- **Agentic effort:** not estimated in the approved pack — record **actuals only** after `implement-story` / agent runs ([Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md) § Agentic actuals).
- **Logic:** Pillar order **01 → 03 → 04 → 02 → 05 → 06** per architecture dependencies (see network).
- **Milestones:** **MS-01 … MS-07** in pillar overview; **MS-07** closes Phase-1 product track.
- **Critical path (draft):** ~**78 WD likely** (~**15.6 weeks** at 1 FTE) plus reserves **SCH-RSV-001…004** and 10% management reserve.

## 4. Develop & control schedule

- **Estimates** and limits: [Schedule-Basis-of-Estimates.md](schedule-baseline/foundation/Schedule-Basis-of-Estimates.md).
- **Reserves:** [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md).
- **Reforecast:** **Human WD** actuals from `implement-story` may replace analogous cells; **agentic** metrics logged separately and never mixed into WD without an explicit rebaseline. CI benchmarks inform validation, not WD by default.
- **Resource/cost:** Duration loads export to **7.C / 7.D** when those packs start.

## 5. Agentic parallel execution (living — added 2026-11-10)

Per `docs/sequence-and-lessons.md` rule 31, cross-cutting execution rules live here, not in the frozen 7.B foundation pack.

| Topic | Authority |
|---|---|
| Policy | [Agentic-Parallel-Execution-Policy.md](../Agentic-Parallel-Execution-Policy.md) |
| Integration queue | [Implementation-Story-Queue.md](../../registers/Implementation-Story-Queue.md) (schedule CP order) |
| Active claims / bake lock | [Project-Status-Register.md](../../registers/Project-Status-Register.md) §5 |
| Worktree claim | `node scripts/provision-story-worktree.mjs <WBS>` |
| `implement-story` | `.claude/skills/implement-story/SKILL.md` (MXC confirmations + Tier A/B) |

**Tier A:** one integration story at a time on the network critical path. **Tier B:** up to three scaffold lanes with `integrates=false`. **Hyper-V:** one sandbox session per agent; serial integration tests on shared host where lessons require it.

## 6. Approved schedule baseline roll-up (2026-11-10)

| Element | Value |
|---|---|
| Integration path | WBS **1.1.1 → … → 1.6.4** per [Schedule-Network-Phase1.md](schedule-baseline/foundation/Schedule-Network-Phase1.md) |
| Likely critical path | **~78 WD** / **~15.6 wks** @ 1 FTE ([Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md)) |
| Reserves | [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) |
| Agentic execution | [§5 Agentic parallel execution](#5-agentic-parallel-execution-living--added-2026-11-10) (living; not in frozen pack) |
| Gate record | [approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json) |
| PMP integration | **Complete (2026-11-10)** — [Project-Management-Plan.md](../Project-Management-Plan.md) §3.2 and §2.6.1 |
| Full PMP lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

This subsidiary plan integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Foundation pack approval uses **`approve-subsidiary-plan`**; integrated PMP lock uses **`approve-pmp`**. **Relative week models and WD ranges are not authorization to execute** — **Stage 8** notice still required.

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json).

**PMP roll-up:** Baseline identifier, manifest **v1.1.0**, approval reference, open **Q-SCH-001…003**, and agentic **actuals-only** rule integrated into [Project-Management-Plan.md](../Project-Management-Plan.md) **2026-11-10** (integrated **`approve-pmp`** lock **2026-11-10**).
