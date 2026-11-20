---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "7.1 Cost Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
  - "resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "cost-baseline/Cost-Foundation-Pack-Manifest.md"
process: "Establish cost estimating basis, contractor rate schedules, staged wave budgets, contingency reserves, and EVM variance controls"
outputs:
  - "Cost-Management-Plan.md"
  - "cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md"
  - "cost-baseline/foundation/Cost-Estimates-by-Category.md"
  - "cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md"
  - "cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md"
status: "Approved"
---

# Cost Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the authorized Cost Baseline (`PMP-BL-v1.0.0`) staged across 5 execution waves.

## 1. Executive summary and financial framework

This Cost Management Plan establishes the financial policies, estimating methodology, contractor billing rate structures, staged budget baselines, and variance controls for MXC Phase 1.

Key financial characteristics:
- **Base Work Package Estimates**: **\$14,665** (90 hours of contractor labor @ \$145–\$177/hr blended + 10.6M AI tokens).
- **Cost Contingency Reserve (15%)**: **\$2,200** (allocated for technical iterations, retry loops, and tuning).
- **Total Cost Baseline**: **\$16,865** (staged across Waves 1 through 5).
- **Management Reserve**: **\$3,500** (held for unforeseen host OS/driver breaking changes).
- **Total Authorized Project Budget**: **\$20,365** (fully within the Project Manager's delegated threshold of **\$25,000**).
- **Estimated Net Savings**: **$\approx \$62,000$ (over $80\%$)** compared to manual software engineering without autonomous agent workers.

---

## 2. Cost foundation pack structure

The full cost baseline model is documented in the foundation pack:
1. **Pillar Overview and Trace**: [Cost-Pillar-Overview-and-Trace.md](cost-baseline/foundation/Cost-Pillar-Overview-and-Trace.md) traces TP-01–06 to financial cost drivers.
2. **Categories & Estimating Basis**: [Cost-Categories-and-Estimating-Basis.md](cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md) defines labor, compute, licensing, and three-point PERT estimation rules.
3. **Cost Estimates by Category**: [Cost-Estimates-by-Category.md](cost-baseline/foundation/Cost-Estimates-by-Category.md) quantifies contractor hours $\times$ rates across all 19 activities and 17 user stories.
4. **Staged Budget and Baseline**: [Cost-Staged-Budget-and-Baseline.md](cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md) details staged cash flows across Waves 1–5, reserves, and release gates.
5. **Variance & Control Protocol**: [Cost-Variance-and-Control-Protocol.md](cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md) establishes EVM tracking ($PV$, $EV$, $AC$, $CV$, $CPI$), thresholds, and corrective action protocols.
6. **Domain Checklist**: [Cost-Domain-Checklist.md](cost-baseline/foundation/Cost-Domain-Checklist.md) confirms PMBOK 8 Finance Performance Domain compliance (**PASS**).

---

## 3. Contractor rate structure and labor valuation

Human labor is valued at competitive market contractor rates for specialized Windows virtualization and systems architecture:

| Role / Specialization | Hourly Contractor Rate | Estimated Hours | Base Labor Valuation |
|---|:---:|:---:|:---:|
| **Project Sponsor / PM (Menno Drescher)** | \$140 – \$160 / hr | 18h | \$2,700 |
| **Lead / System Architect** | \$180 – \$220 / hr | 12h | \$2,400 |
| **Platform / Hyper-V Engineering Lead** | \$150 – \$185 / hr | 16h | \$2,640 |
| **Security & Compliance Officer** | \$160 – \$195 / hr | 10h | \$1,750 |
| **Gateway / Ingress Engineer** | \$140 – \$175 / hr | 10h | \$1,550 |
| **SRE / Autoscaler Engineer** | \$140 – \$175 / hr | 10h | \$1,550 |
| **Quality & Test Coordinator** | \$110 – \$140 / hr | 14h | \$1,750 |
| **Total Contractor Labor** | **Blended: \$159 / hr** | **90h** | **\$14,290** |

---

## 4. Staged budget across schedule execution waves

| Execution wave | Deliverables & WBS packages | Base cost | Contingency | Wave total | Milestone gate |
|---|---|:---:|:---:|:---:|:---:|
| **Wave 1: Base Platform** | WBS 1.0, 2.1, 2.2, 4.1, 6.2 | \$4,625 | \$700 | **\$5,325** | Milestone M1 Entry |
| **Wave 2: Paused State & Image** | WBS 4.2, 5.1, 5.2, 5.3, 6.1, 6.3 | \$3,475 | \$520 | **\$3,995** | Milestone M1 Exit / M2 |
| **Wave 3: Ingress Gateway & Wake** | WBS 3.1, 3.2, 3.3, 7.3 | \$2,405 | \$360 | **\$2,765** | Milestone M3 |
| **Wave 4: Autoscaling & SRE** | WBS 7.1, 7.2, 7.4 | \$1,455 | \$220 | **\$1,675** | Milestone M4 |
| **Wave 5: Integrated Acceptance** | WBS 8.0 | \$2,705 | \$400 | **\$3,105** | Milestone M5 |
| **Total Cost Baseline** | **All 17 User Stories (ACT-01 to 19)** | **\$14,665** | **\$2,200** | **\$16,865** | Full Acceptance Pass |

---

## 5. Financial control, EVM tolerances, and governance limits

1. **Earned Value Management (EVM)**:
   - Performance measured continuously as user stories pass `pr_gate.py`.
   - Tolerance threshold: $\text{CPI} \ge 0.90$. If $\text{CPI} < 0.90$ or $\text{CV} < -\$1,500$, the Project Manager executes root cause analysis and draws from the contingency reserve.
2. **Delegated Authority Compliance**:
   - The entire project budget including all reserves (**\$20,365**) is below the **USD 25,000** limit established in the Project Charter.
   - Any cost variance that would cause total expenditures to exceed USD 25,000 requires an immediate pause and submission of an amended Business Case to the Steering Committee.
