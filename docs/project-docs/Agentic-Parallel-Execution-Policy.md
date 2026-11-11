---
artifact_id: agentic-parallel-execution-policy
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
version: "1.0.0"
effective: "2026-11-10"
owner_role: Project Manager
governance_policy: none
status: draft
depends_on:
  - scope-baseline approved
  - schedule-baseline approved
---

# Agentic parallel execution policy — mxc

Living operational policy for **multiple agents** implementing approved user stories **in parallel** without undetected collision. This document **extends** `.claude/skills/implement-story/SKILL.md` (SIDPA template rule 28) and **does not** replace Stage 8 authorization — see [Stage-8 notice](Status-Reports/Stage-8-Implementation-Authorization-Notice.template.md).

**Schedule authority for integration order:** [Schedule-Network-Phase1.md](management-plans/schedule-baseline/foundation/Schedule-Network-Phase1.md) (not epic folder numeric order alone).

**Schedule metrics:** Approved schedule **WD ranges = human developer effort only**. **Agentic** effort (sessions, parallelism, tool time) is **not estimated** in the schedule baseline; teams **fill actuals** after runs in [Schedule-Baseline-WBS-Forecast.md](management-plans/schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md) § Agentic actuals and [Story-Execution-Register.md](../registers/Story-Execution-Register.md).

## 1. Execution tiers

| Tier | Mode | Parallelism | AC / `implement-story` complete? |
|---|---|---|---|
| **A — Integration** | Full `implement-story` on schedule CP | **One active story** at a time per integration queue | Yes — must pass contracts + PR |
| **B — Scaffold** | Contract RED + mocks; `integrates=false` in Intent | Up to **3** concurrent lanes | No — merge only with integration story or as prereq PR |
| **C — Docs / registers** | Governance, registers, ADR copies | Parallel with A/B if disjoint paths | N/A |

**Rule:** Tier **A** owns the **next** WBS ID in [Implementation-Story-Queue.md](../registers/Implementation-Story-Queue.md). Tier **B** must name an explicit **integration-unlock** WBS (when Tier A reaches it, scaffold merges).

## 2. Story identity & git isolation

| Field | MXC convention |
|---|---|
| **WBS ID (authoritative)** | From epic `**WBS ID:**` lines (e.g. `1.2.1`) |
| **Branch** | `feat/story-<WBS>` → `feat/story-1.2.1` |
| **Worktree directory** | `../mxc-story-<WBS>` (sibling of repo root) |
| **Base branch** | `feat/hyperv-v2-rebased` (confirm with `git branch --show-current` before first use) |
| **Claim** | `node scripts/provision-story-worktree.mjs <WBS>` — failure = already claimed |
| **Legacy `US-xx.y` IDs** | `npm run story:done` accepts WBS; maps `1.1.1` ↔ epic Story `1.1` for contract search |

## 3. Integration story queue (Tier A)

Order follows **schedule critical path**, not epic folder order:

`1.1.1 → 1.1.2 → 1.3.1 → 1.3.2 → 1.4.1 → 1.4.2 → 1.4.3 → 1.2.1 → 1.2.2 → 1.2.3 → 1.5.1 → 1.5.2 → 1.5.3 → 1.6.1 → 1.6.2 → 1.6.3 → 1.6.4`

Authoritative ordered list: [Implementation-Story-Queue.md](../registers/Implementation-Story-Queue.md).

**Before starting Tier A:** run `validate-intent-foundation` for that story's ADR/BRD/FDD/epic chain when Stage 8 notice is in force (or sponsor waives for dry-run scaffold only).

## 4. Parallel lanes (Tier B) — allowed patterns

| Lane | Example WBS (scaffold only) | Collision notes |
|---|---|---|
| Ingress unit tests / gateway skeleton | `1.2.x` before `1.4.3` | **No** live pause integration; mock `pool_lease` |
| Image pipeline scripts (no prod catalog) | `1.3.1` partial | **No** concurrent VHDX bake on same host |
| Pool policy unit tests | `1.6.x` | **No** shared `wxc-exec` pool state with Tier A |
| Rust module contracts | any | Separate files under agreed ownership (below) |

**Max concurrent Tier B lanes:** 3. **Max Tier A:** 1.

## 5. Runtime isolation (Hyper-V)

Mandatory for Tier **A** and any Tier **B** touching guests:

1. MXC sandbox MCP: `sync_workspace_to_guest` before work; `disposable=True` for speculative runs.
2. **One agent ↔ one sandbox session** — no two agents share a pool name (`prod-adpa`, etc.) on the same host.
3. Heavy VM suites (**1.4.x**, **1.2.x** integration, **1.6.x** load) **serial** on production Hyper-V host (see `docs/hyperv/architecture/LESSONS_LEARNED.md`).

## 6. Code ownership & merge queue

| Path prefix | Primary epic / agent lane | Merge rule |
|---|---|---|
| `src/tools/wxc/` | Pool / lifecycle (006, 004) | Single merge queue; rebase daily |
| Ingress / gateway (`jit_ingress`, docs paths in FDD-002) | 002 | Coordinate with pool API changes |
| Image bake / `scripts/hyperv/` image | 003 | Exclusive bake lock in [Project-Status-Register.md](../registers/Project-Status-Register.md) §5 |
| `docs/hyperv/GOLDEN_IMAGE_REGISTRY.md` | 003 | Human or single release agent only |

Foreign contract breaks (Step 6 full suite): see `heal-contract-failure` — **no** parallel heal on same branch.

## 7. Contract & validation (polyglot)

| Layer | Tool | When |
|---|---|---|
| Orchestration / gateway (future) | `node --test tests/contracts/**/*.test.js` | Step 6 if JS contracts exist |
| Rust control plane | `cargo test -p <crate>` (per story SKILL) | Step 6 always for Rust deliverables |
| Hyper-V integration | Sandbox MCP + PS/Python harnesses named in FDD | Tier A only |
| Repo gate | `npm run test` → `scripts/run-contracts.mjs` | CI / pre-PR |

See [tests/contracts/README.md](../../tests/contracts/README.md).

## 8. Registers & orientation

| Register | Use |
|---|---|
| [Project-Status-Register.md](../registers/Project-Status-Register.md) | **Who** owns Tier A/B; bake lock; session checkpoint |
| [Implementation-Story-Queue.md](../registers/Implementation-Story-Queue.md) | **What** is next on CP |
| [Story-Execution-Register.md](../registers/Story-Execution-Register.md) | **Which** `implement-story` steps completed |

Agents **must** read §1 and §5 of Project-Status-Register before claiming a story.

## 9. Explicit non-goals (v1)

- **PIL-11** competency bidding / swarm task marketplace — not built.
- Parallel **Tier A** on two integration stories — forbidden.
- Autonomous merge to `feat/hyperv-v2-rebased` — PR required (implement-story Step 8).

## 10. Open preparation gaps

| ID | Gap | Owner | Closure |
|---|---|---|---|
| APX-001 | Stage 8 Implementation Authorization not issued | Sponsor | Sign notice |
| APX-002 | No story has run `implement-story` — Rust contract paths unconfirmed | Platform | Story `1.1.1` |
| APX-003 | Schedule pack not subsidiary-approved | PM | **closed (2026-11-10)** |
