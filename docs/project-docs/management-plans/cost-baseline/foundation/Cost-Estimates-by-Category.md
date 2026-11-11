---
artifact_id: cost-foundation-estimates-by-category
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.D-2
pmbok_process: Estimate Costs
depends_on:
  - 7.D-1
  - schedule-baseline approved
  - resource-baseline approved
---

# Cost Estimates by Category — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d2-estimates-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-cost-7d2-estimates-2026-11-10.adjudication.json).

## CAT-LAB — per WBS (lead specialist rate)

| WBS ID | CAT | Lead | WD (low / likely / high) | h (likely) | Rate (EUR/h) | Cost low | Cost likely | Cost high | Basis |
|---|---|---|---|---|---|---|---|---|---|
| 1.1.1 | CAT-LAB | R-PLT | 2 / 4 / 5 | 24 | 110 | €1,320 | €2,640 | €3,300 | Forecast + role catalogue |
| 1.1.2 | CAT-LAB | R-PLT | 2 / 3 / 4 | 18 | 110 | €1,320 | €1,980 | €2,640 | |
| 1.3.1 | CAT-LAB | R-REL | 4 / 7 / 10 | 42 | 100 | €2,400 | €4,200 | €6,000 | |
| 1.3.2 | CAT-LAB | R-REL | 2 / 4 / 6 | 24 | 100 | €1,200 | €2,400 | €3,600 | |
| 1.4.1 | CAT-LAB | R-PLT | 2 / 4 / 6 | 24 | 110 | €1,320 | €2,640 | €3,960 | |
| 1.4.2 | CAT-LAB | R-PLT | 3 / 5 / 7 | 30 | 110 | €1,980 | €3,300 | €4,620 | |
| 1.4.3 | CAT-LAB | R-PLT | 3 / 5 / 8 | 30 | 110 | €1,980 | €3,300 | €5,280 | |
| 1.2.1 | CAT-LAB | R-PLT | 4 / 6 / 8 | 36 | 110 | €2,640 | €3,960 | €5,280 | |
| 1.2.2 | CAT-LAB | R-PLT | 2 / 4 / 5 | 24 | 110 | €1,320 | €2,640 | €3,300 | |
| 1.2.3 | CAT-LAB | R-PLT | 3 / 5 / 7 | 30 | 110 | €1,980 | €3,300 | €4,620 | |
| 1.5.1 | CAT-LAB | R-SEC | 3 / 5 / 6 | 30 | 115 | €2,070 | €3,450 | €4,140 | |
| 1.5.2 | CAT-LAB | R-SEC | 4 / 6 / 8 | 36 | 115 | €2,760 | €4,140 | €5,520 | |
| 1.5.3 | CAT-LAB | R-SEC | 2 / 4 / 5 | 24 | 115 | €1,380 | €2,760 | €3,450 | |
| 1.6.1 | CAT-LAB | R-SRE | 2 / 4 / 5 | 24 | 110 | €1,320 | €2,640 | €3,300 | |
| 1.6.2 | CAT-LAB | R-SRE | 2 / 4 / 5 | 24 | 110 | €1,320 | €2,640 | €3,300 | |
| 1.6.3 | CAT-LAB | R-SRE | 2 / 3 / 5 | 18 | 110 | €1,320 | €1,980 | €3,300 | |
| 1.6.4 | CAT-LAB | R-SRE | 2 / 4 / 5 | 24 | 110 | €1,320 | €2,640 | €3,300 | |
| **1.0 CP** | | | **~44 / 78 / ~102** WD | **468** | — | **~€28.5k** | **€50,610** | **~€66.2k** | Sum of rows (low/high via WD×6×rate) |

**Cost low/high** = sum of (WD low or high × **6** × lead contractor rate) per row.

## CAT-LAB-OV — governance overlay (likely)

**Contractor-market ROM** for governance work **not on the CP serial path**. **Someone pays** for PM and governance — captured here as **sponsor-funded / project** cost at market rates (no payroll book).

| Item | Role | WD (likely) | h | Rate (EUR/h) | Cost likely | Who pays (planning) |
|---|---|---|---|---|---|---|
| Contract review overlay | R-QA | 8 | 48 | 90 | €4,320 | Project / procured QA if SOW |
| PM — subsidiary gates, registers, Stage 8 prep | R-PM | 4 | 24 | 95 | **€2,280** | **Sponsor / PM** (imputed at contractor PM rate) |
| Architecture spikes | R-ARC | 2 | 12 | 125 | €1,500 | Project / fractional contractor |
| **Subtotal OV** | | **14** | **84** | — | **€8,100** | Included in **€58,710** performance baseline |

**PM note:** PM effort is **not** on the integration schedule and **hours are not logged** in registers; **€2,280** still appears in the cost baseline as the **fair planning value** of PM work for Phase-1 (equivalent to ~4 WD at **€95/h**). Actual sponsor time may differ; rebaseline on evidence, not timesheets.

## CAT-CONT — schedule reserve cost envelope (if fully consumed)

| Reserve ID | WD range | h (mid) | Planning rate | Cost envelope (EUR) | Trigger |
|---|---|---|---|---|---|
| SCH-RSV-001 | 5–10 | 30–60 | 110 | €3,300 – €6,600 | Pause metrics |
| SCH-RSV-002 | 5–15 | 30–90 | 100 | €3,000 – €9,000 | VHDX catalog |
| SCH-RSV-003 | 3–7 | 18–42 | 110 | €1,980 – €4,620 | Dual routing |
| SCH-RSV-004 | 2–5 | 12–30 | 95 | €1,140 – €2,850 | Audit latency |
| SCH-RSV-MGT | **~4–8** (10% CP) | 24–48 | 110 | **~€2,640 – €5,280** | PM change |
| **Contingency envelope** | | | | **~€18k – €28k** | Not auto-spent |

## CAT-INFRA / CAT-TOOL / CAT-AGT (Phase 1)

| CAT | Estimate likely | Range | Note |
|---|---|---|---|
| CAT-INFRA | **€0** | 0 – €2,000 | Placeholder opex if storage tier upgrade required |
| CAT-TOOL | **€71 / mo** | **~€256** Phase-1 | Recurring subscriptions — **Q-CST-002** table below |
| CAT-AGT | **N/A** | Usage overage | Token/API overage beyond subscriptions — actuals only |

### Q-CST-002 — CAT-TOOL (recurring subscriptions)

**Price date:** **2026-11-10** (sponsor). **EUR / month**, ex. VAT unless invoices state otherwise.

| Service | Monthly (EUR) | Assigned use | Notes |
|---|---|---|---|
| **Cursor** | **16** | IDE + agent (V-AGT / Tier A/B) | Seat for repo work |
| **Gemini Antigravity** | **25** | Agent / assistant lane | Per sponsor plan name |
| **Claude Code** | **20** | Agentic coding assist | Complements `implement-story` |
| **GitHub** (Basic plan) | **10** | Repo, PRs, Actions baseline | Remote + integration queue |
| **Subtotal recurring** | **71** | — | Fixed monthly burn (sponsor **2026-11-10**) |

**Phase-1 planning (CP ~15.6 wks ≈ 3.6 mo):** **€71 × 3.6 ≈ €256** likely subscription cost over integration window (separate from **€58,710** labor performance baseline).

| Topic | Explanation |
|---|---|
| **What CAT-TOOL covers** | Recurring **subscription** fees above — not embedded in **CAT-LAB** hourly rates. |
| **What it does not cover** | **Hyper-V host** (CAT-INFRA), **labor** (**CAT-LAB** / **CAT-LAB-OV**), **metered API overage** beyond plan (**CAT-AGT**). |
| **vs performance baseline** | **€58,710** = labor only; **€71/mo** (**~€256** Phase-1) = parallel **CAT-TOOL** opex — sponsor pays subscriptions directly. |
| **Variance** | Actual invoice must match **€71/mo** ± plan changes; new tool → rebaseline manifest. |
| **Status** | **Closed (2026-11-10)** — amounts **ratified** by sponsor; track monthly actuals against table. |

## Summary roll-up (ex. VAT)

| Roll-up | Low | Likely | High | Confidence |
|---|---|---|---|---|
| **CAT-LAB** (CP) | ~€28,500 | **€50,610** | ~€66,200 | Low–Med |
| **+ CAT-LAB-OV** | — | **€8,100** | — | Med |
| **Performance baseline (likely)** | | **€58,710** | | |
| **+ CAT-TOOL** (subs, ~3.6 mo) | | **~€256** | | High |
| **Planning labor + subs (likely)** | | **~€58,966** | | |
| **+ CAT-CONT** (if all reserves burn) | | +€18k – €28k | | Low |
| **Indicative ceiling** (labor + subs + full CONT) | | **~€77k – €87k** + subs | | Low |

## Reconciliation

- **Schedule:** **78 WD likely** on CP ≡ **468 h** ≡ **€50,610** labor — matches resource pack ROM.
- **Scope:** Each row traces to [Scope-WBS-Dictionary.md](../../scope-baseline/foundation/Scope-WBS-Dictionary.md).
- **Resource:** **CAT-LAB** = CP lead labor; **CAT-LAB-OV** = governance ROM (**€8,100**, includes **€2,280** PM); hours optional, **EUR** in baseline for “someone pays.”
- **Committed vs contingent:** **CAT-LAB** + **CAT-LAB-OV** = performance baseline; **CAT-CONT** = contingent until reserve triggered.

## Open cost items

| ID | Question | Owner | Status |
|---|---|---|---|
| Q-CST-001 | Sponsor / PM labor cost | Sponsor | **closed** — **€2,280** in **CAT-LAB-OV** (imputed); hours unlogged |
| Q-CST-002 | CAT-TOOL subscriptions **€71/mo** | Sponsor | **closed (2026-11-10)** — Cursor €16, Gemini Antigravity €25, Claude Code €20, GitHub Basic €10 |
| Q-CST-003 | Funding authorization | Sponsor | **closed** — via **`approve-subsidiary-plan`** (cost/resource) + **`approve-pmp`**; no separate funding letter |
