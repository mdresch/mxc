---
artifact_id: resource-foundation-role-catalogue
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-1
pmbok_process: Plan Resource Management
depends_on:
  - 7.C-0P
  - schedule-baseline approved
---

# Resource Role Catalogue — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c1-role-catalogue-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c1-role-catalogue-2026-11-10.adjudication.json).

**Rate basis:** **EUR**, price date **2026-11-10**. **Authoritative for planning and ROM:** **market-conform contractor** hourly rates (procured day-rate ÷ 8 h, **ex. VAT**, EU/NL software engineering bands). **Payroll loaded rates:** **N/A** — no employer payroll cost data available; do not invent loaded rates. **R-PM / sponsor PM:** **not on the integration schedule**; **hours not logged** — cost baseline still carries **€2,280** (4 WD × **€95/h**) in **CAT-LAB-OV** so planning reflects that **someone pays** for PM (sponsor-funded imputed value).

## Role summary (execution)

| Role ID | Title | Class | Primary WBS / pillar | Activity owner (WBS dict.) | Decision authority |
|---|---|---|---|---|---|
| **R-PLT** | Senior platform engineer | Human — payroll or contractor | **1.1**, **1.2**, **1.4** (TP-01, 02, 04) | Platform | Story technical design, merge to integration branch, sandbox runs |
| **R-REL** | Release / image engineer | Human — payroll or contractor | **1.3** (TP-03) | Release | VHDX baseline, checkpoint publish, image pipeline |
| **R-SEC** | Security operations engineer | Human — payroll or contractor | **1.5** (TP-05) | SecOps | Egress policy, session disk posture, sterility AC |
| **R-SRE** | Site reliability engineer | Human — payroll or contractor | **1.6** (TP-06) | SRE | Pool sizing, hygiene metrics, scale policies |
| **R-QA** | Quality / contract engineer | Human — payroll or contractor | All **1.N.S** (supporting) | Platform (matrix) | Contract RED/GREEN, CI gate interpretation |
| **R-PM** | Project manager | Human — payroll | **2.0**, milestones | PM | Subsidiary gates, rebaseline, Stage 8 notice |
| **R-ARC** | Solution architect (advisory) | Human — contractor or fractional | Cross-pillar | Sponsor | ADR alignment, escalate cross-pillar conflicts |
| **V-AGT** | Agentic dev assistant | Virtual — tooling | Tier A/B per [Agentic-Parallel-Execution-Policy.md](../../../Agentic-Parallel-Execution-Policy.md) | Platform | **No** baseline hourly rate; actuals only |

## Skills and competencies by role

### R-PLT — Senior platform engineer

| Competency area | Required proficiency | Evidence / certification (optional) |
|---|---|---|
| Windows Server / Hyper-V Gen2 | Advanced — VM config, VMBus, synthetic devices | ADR-001; host admin experience |
| Rust systems programming | Advanced — async, error handling, crate boundaries | `implement-story` Rust deliverables |
| PowerShell / host automation | Working — Hyper-V cmdlets, sandbox workflow | Repo scripts, pool operations |
| Networking — ingress, load balancing, wake paths | Working — TTFB, 502/504 elimination, dual routing | Epic 002, HYP-mxc-004 |
| Performance measurement | Working — resume &lt;300 ms, benchmarks | `benchmark_jit_wake.py` |
| Git / PR workflow, contract tests | Working — polyglot contracts | Tier A integration queue |

### R-REL — Release / image engineer

| Competency area | Required proficiency | Evidence |
|---|---|---|
| VHDX / differencing disk lifecycle | Advanced | ADR-003, BEN-08 |
| Image hardening and reproducible builds | Working | Story 3.1–3.2 AC |
| Checkpoint / warm-pool handoff to platform | Working | MS-02 milestone |
| Windows imaging tooling (DISM, sysprep awareness) | Working | Production base image epic |

### R-SEC — Security operations engineer

| Competency area | Required proficiency | Evidence |
|---|---|---|
| Session isolation and ephemeral disks | Advanced | ADR-005, epic 005 |
| Egress control / whitelist design | Working | AC-02.3, Story 5.2 |
| Threat-aware defaults on sandbox hosts | Working | Session sterility stories |
| Compliance-oriented documentation | Working | Audit-oriented AC closure |

### R-SRE — Site reliability engineer

| Competency area | Required proficiency | Evidence |
|---|---|---|
| Pool buffer and surge semantics | Advanced | Epic 006, watermark pool |
| Metrics, hygiene, scale-down safety | Working | Stories 6.3–6.4 |
| Operational runbooks and observability | Working | MS-06 milestone |
| Coordination with platform on shared host | Working | Q-SCH-003 multi-resource model |

### R-QA — Quality / contract engineer

| Competency area | Required proficiency | Evidence |
|---|---|---|
| Contract-first testing (JS/Rust) | Advanced | `tests/contracts/`, `implement-story` |
| CI interpretation and flake triage | Working | Post–Stage 8 pipelines |
| Acceptance traceability to epic AC | Working | Scope validate scope |

### R-PM — Project manager

| Competency area | Required proficiency | Evidence |
|---|---|---|
| SIDPA / PMBOK subsidiary gates | Working | `approve-subsidiary-plan`, registers |
| Schedule + resource rebaseline | Working | 7.B / 7.C packs |
| Stakeholder escalation | Working | Charter, Stage 8 notice |

### R-ARC — Solution architect (advisory)

| Competency area | Required proficiency | Evidence |
|---|---|---|
| Six-pillar architecture coherence | Expert — advisory | ADR-001–006 suite |
| Trade-off facilitation across pillars | Working | Network CP order TP-01→03→04→02→05→06 |

## Hourly rate estimates (planning)

| Role ID | Payroll loaded (EUR/h) | Contractor market (EUR/h) — **planning ROM** | Contractor low / high | Source |
|---|---|---|---|---|
| **R-PLT** | **N/A** | **110** | 95–140 | Market-conform NL senior platform / systems dev (sponsor accepted 2026-11-10) |
| **R-REL** | **N/A** | **100** | 85–125 | Image / release engineering band |
| **R-SEC** | **N/A** | **115** | 100–145 | Security-specialist premium |
| **R-SRE** | **N/A** | **110** | 95–135 | SRE mid-senior band |
| **R-QA** | **N/A** | **90** | 75–110 | Test / quality engineering |
| **R-PM** | **N/A** | **95** | 80–115 | PM / delivery lead |
| **R-ARC** | **N/A** | **125** | 110–160 | Fractional architect (day-rate ÷ 8 h) |
| **V-AGT** | **N/A** | **N/A** | — | Token / subscription actuals — cost pack **7.D** |

**Procurement note:** ROM and **7.D** labor use **contractor market** column only. Engaged contractors route through [Procurement-Management-Plan.md](../../Procurement-Management-Plan.md). Sponsor labor: log **hours** in execution registers; **EUR payroll valuation optional** until Finance publishes loaded rates.

## Lead specialist and reporting specialists

When a story needs more than one discipline, staffing uses exactly **one lead specialist** per Tier A integration story plus zero or more **reporting specialists** who **report to that lead** for the duration of the WBS (task stand-up, partial deliverables, review fixes—not necessarily HR line management).

| Rule | Definition |
|---|---|
| **Lead specialist** | Owns Tier A queue claim, `implement-story` integration PR, and technical tie-break for that WBS |
| **Reporting specialist** | Contributes scoped work to the lead; escalates blockers to lead; does not merge integration PR without lead sign-off |
| **WBS accountable (RACI A)** | Unchanged—[Scope-WBS-Dictionary.md](../../scope-baseline/foundation/Scope-WBS-Dictionary.md) owner (Platform, Release, SecOps, SRE) |
| **Solo story** | Lead only; **R-QA** may still report to lead for contracts when marked “optional QA” |

**Virtual (V-AGT):** Reports to the **lead specialist** for the active WBS (Tier A/B policy).

## WBS staffing matrix (integration queue)

| WBS ID | Work package | Lead specialist | Reporting to lead | RACI **A** (WBS owner) |
|---|---|---|---|---|
| 1.1.1 | Gen2 isolation boundary | **R-PLT** | R-QA (contracts) | Platform |
| 1.1.2 | Windows subsystems on guest | **R-PLT** | R-QA | Platform |
| 1.3.1 | Clean production VHDX | **R-REL** | R-PLT (guest/platform fit), R-QA | Release |
| 1.3.2 | Warm baseline checkpoint | **R-REL** | R-PLT (pool handoff), R-QA | Release |
| 1.4.1 | Zero idle CPU at Paused | **R-PLT** | R-SRE (metering pattern), R-QA | Platform |
| 1.4.2 | Trimmed paused footprint | **R-PLT** | R-SRE, R-QA | Platform |
| 1.4.3 | Sub-300 ms resume | **R-PLT** | R-SRE (benchmarks), R-QA | Platform |
| 1.2.1 | Cold wake TTFB | **R-PLT** | R-SRE (SLO framing), R-QA | Platform |
| 1.2.2 | No wake 502/504 | **R-PLT** | R-SRE, R-QA | Platform |
| 1.2.3 | Dual routing rules | **R-PLT** | R-SEC (edge policy), R-ARC (HYP-mxc-004), R-QA | Platform |
| 1.5.1 | Ephemeral session disk | **R-SEC** | R-PLT (Hyper-V disk path), R-QA | SecOps |
| 1.5.2 | Egress whitelist | **R-SEC** | R-PLT (host plumbing), R-QA | SecOps |
| 1.5.3 | Discard and reproduce | **R-SEC** | R-PLT, R-REL (image reuse boundaries), R-QA | SecOps |
| 1.6.1 | Buffer replenishment | **R-SRE** | R-PLT (control plane), R-REL (checkpoint), R-QA | SRE |
| 1.6.2 | Surge expansion | **R-SRE** | R-PLT, R-QA | SRE |
| 1.6.3 | Wake hygiene | **R-SRE** | R-PLT (wake path), R-QA | SRE |
| 1.6.4 | Scale down | **R-SRE** | R-PLT, R-PM (governance sign-off on cooldown), R-QA | SRE |
| MS-07 | Phase-1 baseline | **R-PM** | All **leads** from rows above (status rollup) | PM |

**RACI shorthand:** Lead = **R** on execution; reporting specialists = **R** on their slice, **C** on integration PR; **A** = table column; **I** = R-PM. **R-ARC** is consult-only unless listed as reporting.

## Pillar rollup (who leads which milestone path)

| Milestone | Lead specialist (primary) | Typical reporting chain |
|---|---|---|
| MS-01 | R-PLT | R-QA |
| MS-02 | R-REL | R-PLT → R-REL lead; R-QA → R-REL lead |
| MS-03 | R-PLT | R-SRE, R-QA → R-PLT lead |
| MS-04 | R-PLT | R-SRE, R-SEC (1.2.3), R-ARC, R-QA → R-PLT lead |
| MS-05 | R-SEC | R-PLT, R-REL (1.5.3), R-QA → R-SEC lead |
| MS-06 | R-SRE | R-PLT, R-REL, R-QA → R-SRE lead |

## Responsibility model

- **One lead specialist** per active Tier A WBS; reporting specialists may work Tier B scaffolds that **merge only through the lead’s** integration story unless `integrates=false` policy says otherwise.
- **One accountable human** per story per WBS dictionary (RACI **A**)—usually matches pillar owner; the **lead** may be the same person wearing the lead role hat (common under staffing **S1**).
- **Virtual (V-AGT):** augments lead/reporting work; does not replace lead on acceptance evidence or Hyper-V integration sign-off.
- Reporting conflicts (two specialists claiming lead) escalate to **R-PM** and WBS **A** within 1 WD.

## Open items

| ID | Question | Owner | Status |
|---|---|---|---|
| Q-RES-001 | Payroll loaded EUR rates | Finance | **closed (N/A)** — not available; contractor market rates accepted for planning |
| Q-RES-002 | Staffing model (S1/S2 + lead/reporting matrix) | PM | **closed (2026-11-10)** — sponsor accepted draft; no estimate rebaseline |
| Q-RES-003 | Contractor SOW when engaging external roles | PM + Procurement | open — ROM assumes market contractor; payroll mix N/A |
