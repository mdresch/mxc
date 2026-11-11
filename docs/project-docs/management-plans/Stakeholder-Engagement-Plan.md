---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "13.2 Plan Stakeholder Engagement"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-pmp
pmp_baseline: "PMP-BL-v1.0.0"
inputs:
  - "Project-Charter.md"
  - "Stakeholder-Register.md"
  - "Business-Case.md"
process: "Plan and formalize Stakeholder Engagement Plan"
outputs:
  - "Stakeholder-Engagement-Plan.md"
---

# Stakeholder Engagement Plan — mxc

> **PMBOK 8 Process:** `13.2 Plan Stakeholder Engagement` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Stakeholder-Register.md](../Stakeholder-Register.md), [Project-Charter.md](../Project-Charter.md)

## 1. Purpose & scope

Defines how stakeholders are **engaged**, **consulted**, **informed**, and **escalated to** for Phase-1 **mxc** under **`PMP-BL-v1.0.0`**. Complements the register with strategies and approval touchpoints.

## 2. Stakeholder roster (Phase 1)

| ID | Stakeholder | Role | Interest / influence | Current engagement level | Target (Phase 1) |
|---|---|---|---|---|---|
| **SH-01** | Menno Drescher | Product owner / sponsor / architect | High / High | Leading | **Manage closely** — gate acceptor |
| **SH-02** | SecOps consumers | Security operations | Medium / High | Informed via specs | **Keep satisfied** — AC on 1.5.x |
| **SH-03** | SRE / platform operators | Operations | Medium / Medium | Informed via specs | **Keep informed** — pool/wake stories |
| **SH-04** | PM (governance) | PMBOK steward | High / Medium | Active | **Manage closely** — registers, subsidiary gates |
| **SH-05** | R-QA / verification | Quality | Medium / Medium | Planned | **Consult** at QG-02/03 |
| **SH-06** | V-AGT (agentic lane) | Virtual implementer | Medium / Low | Active in dev | **Inform** — no approval authority |

*SH-04…06 formalized for Stage 8 template alignment; update roster when charter is fully gated.*

## 3. Engagement strategies

| ID | Strategy | Tactics |
|---|---|---|
| SH-01 | Sponsor decisions on baseline, funding, Stage 8 | `approve-subsidiary-plan`, `approve-pmp`, cost Q-CST closures |
| SH-02 | Early security review on egress / session stories | SecOps review checkpoint before 1.5.2 merge |
| SH-03 | Operational readiness checks on 1.6.x | Harness results + status register |
| SH-04 | Single orientation surface | [Project-Status-Register.md](../../registers/Project-Status-Register.md) |
| SH-05 | Contract-first quality | RED/GREEN discipline per quality plan |
| SH-06 | Bounded agent parallelism | [Agentic-Parallel-Execution-Policy.md](../Agentic-Parallel-Execution-Policy.md) |

## 4. Human approval gates (stakeholder touchpoints)

| Gate | Policy | Who must accept |
|---|---|---|
| Foundation packs 7.A–7.D | `approve-subsidiary-plan` | Sponsor (human acceptance) |
| Integrated PMP | `approve-pmp` | Sponsor |
| Stage 8 execution | Stage 8 notice | Sponsor + PM attestation |
| Story implementation | `implement-story` | Per story owner + QA where required |
| Adaptation / rebaseline | Adaptation plan + governance | Sponsor on material change |

Agents and automation **propose**; they do **not** satisfy human approval gates.

## 5. Unresolved stakeholder gaps

| ID | Gap | Action |
|---|---|---|
| Q-SCOPE-002 / charter | Charter not fully gated | Complete `approve-charter` when ready; refresh SH roster |
| Q-SCOPE-004 | Benefits adjudication | Link sponsor success metrics to engagement cadence |
| Register drift | Stage 8 template lists SH-01–06 | Keep [Stakeholder-Register.md](../Stakeholder-Register.md) aligned with this plan at **`approve-pmp`** |

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | **§2.13.2**, **§3.9** |
| Communications cross-ref | [Communications-Management-Plan.md](Communications-Management-Plan.md) |
| Lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

Stakeholder engagement planning is verified under **`approve-pmp`**. Engagement level may rise when external operators depend on production JIT paths.

**Status:** **Approved (2026-11-10)** — rolled into PMP.
