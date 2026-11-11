---
artifact_id: scope-foundation-project-scope-statement
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.A-1
pmbok_process: Define Scope
depends_on:
  - 7.A-0P
---

# Project Scope Statement — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a1-scope-statement-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-scope-7a1-scope-statement-2026-11-10.adjudication.json).

## Purpose and objectives

**Purpose:** Deliver the MXC JIT Hyper-V sandbox so ADPA/SIDPA-class workloads run in **scale-to-zero**, **hardware-isolated**, **sterile** Windows guests with sub-second wake and pool hygiene.

**Objectives (authorized by accepted ADRs 001–006):**

1. Replace shared-kernel containers with **Type-1 Hyper-V Generation 2** guests (ADR-001).
2. **Buffer ingress** while guests are Paused and meet first-byte and error budgets (ADR-002).
3. Ship a **production base image** separate from developer images (ADR-003).
4. Keep guests **Paused** with trim-before-suspend and measured resume (ADR-004).
5. Run sessions on **transient differencing disks** with **egress whitelist** (ADR-005).
6. Operate a **watermark pool** with replenish and wake hygiene (ADR-006).

## Product and project scope

**In scope (product — WBS 1.x):**

| ID | Deliverable | Primary specs |
|---|---|---|
| 1.1 | Isolation & Gen2 platform | ADR/BRD/FDD/epic **001**; `src/mxc-sdk` Hyper-V backend; bake scripts |
| 1.2 | Ingress gateway | ADR **002**; `scripts/hyperv/dev_harness/jit_ingress_gateway.py`; MCP ingress tools |
| 1.3 | Production image supply | ADR **003**; `bake_production_adpa_image.ps1`; registry JSON |
| 1.4 | Paused RAM standby | ADR **004**; pool pause/resume in SDK |
| 1.5 | Session sterility & network | ADR **005**; differencing disk; `configure_port_acls.ps1` |
| 1.6 | Pool watermarks & hygiene | ADR **006**; `pool.rs`; velocity burst / replenish behavior |

**In scope (project management):** SIDPA lifecycle docs, governance gates, subsidiary management plans, contract tests (`tests/`), and architecture suite under `docs/hyperv/architecture/`.

**Project work excluded from product WBS:** PMBOK document maintenance, Second Brain vault sync (optional toolchain), and unrelated MXC SDK backends (WSLC, seatbelt, etc.) except where Hyper-V path requires shared APIs.

## Exclusions

| Excluded item | Reason / authority | Reconsideration trigger |
|---|---|---|
| Shared-kernel container as production host for confidential records | ADR-001; Business Case Alt. 3 | New ADR if bar changes |
| Always-on VM as default economic model | Spark; ADR-004 | Different SLA ADR |
| Shipping dev toolchains on production golden image | ADR-003 | Charter amendment |
| Autonomous scope approval without human gate | All `approve-*` policies | Never—by governance invariant |
| Currency ROI / license savings claims | Business Case refusal | New benefits gate only |
| Unnamed MFA / whole-guest discard product | `Project-Details-Not-In-ADR.md` | New ADR or epic |

## Constraints, assumptions, and dependencies

| Type | Statement | Source / owner | Validation status |
|---|---|---|---|
| Constraint | `pmp_baseline: PMP-BL-v1.0.0` on all Stage 7 artifacts | PMP § invariant 6 | Active |
| Constraint | Hyper-V Type-1 on Windows Server 2025 host | Spark; ADR-001 | Engineering |
| Assumption | Suite `docs/hyperv/architecture/*.md` remains architecture reference; lifecycle ADRs are governing copies | ADR suite cross-links | Documented |
| Dependency | Host Hyper-V, synthetic switch, credentials registration | FDD-002/005/006 | Partially implemented |
| Dependency | Business case approved; charter/benefits not fully gated | Gates folder | **Open**—I1 stakeholder register draft only |

## Acceptance conditions

- Each WBS package 1.1–1.6 has **Approved** BRD, FDD, and epic with gate citations (met 2026-10-30).
- **Accepted** ADR for each pillar (met).
- Each user story has a WBS ID **`1.{pillar}.{story}`** (17 packages); see [Scope-WBS-Dictionary.md](Scope-WBS-Dictionary.md).
- Story-level acceptance defers to epic AC and contract tests; **no story marked `implement-story` complete** yet.
- Scope pack **approved (2026-11-10)** via **`approve-subsidiary-plan`**; integrated PMP lock still requires **`approve-pmp`**.

## Open scope decisions

| ID | Decision needed | Owner | Status |
|---|---|---|---|
| Q-SCOPE-001 | Adjudicate ideation + benefits before charter-locked scope | Menno Drescher | open |
| Q-SCOPE-002 | Close `BEN-08` with real `winserv2025-prod-adpa.vhdx` in catalog | Platform | open |
| Q-SCOPE-003 | Name MFA / second-factor product for ingress wake | SecOps | open |
