---
artifact_id: cost-foundation-staged-budget-baseline
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.D-3
pmbok_process: Develop Budget
depends_on:
  - 6.D-2
---

# Staged Budget and Cost Baseline — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Reconciles work package cost estimates across the 5 schedule execution waves, defining the Cost Baseline and authorized reserves.

## 1. Staged budget breakdown across schedule execution waves

| Stage / Wave | Included WBS & activities | Base contractor labor | AI compute tokens | Contingency reserve (15%) | Wave cost baseline (USD) | Cumulative baseline (USD) | Release gate condition |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **Wave 1: Base Platform** | WBS 1.0, 2.1, 2.2, 4.1, 6.2 (ACT-01 to 04, 06) | \$4,540 (28h) | \$85 (2.4M tokens) | \$700 | **\$5,325** | \$5,325 | Gate 6.B-0 pass & Milestone M1 entry |
| **Wave 2: Paused State & Image** | WBS 4.2, 5.1, 5.2, 5.3, 6.1, 6.3 (ACT-05, 07–11) | \$3,360 (20h) | \$115 (3.2M tokens) | \$520 | **\$3,995** | \$9,320 | Milestone M1 achieved (Warm checkpoint verified) |
| **Wave 3: Ingress Gateway & Wake** | WBS 3.1, 3.2, 3.3, 7.3 (ACT-12 to 15) | \$2,325 (15h) | \$80 (2.2M tokens) | \$360 | **\$2,765** | \$12,085 | Milestone M2 achieved (Sterility & resume verified) |
| **Wave 4: Autoscaling & SRE** | WBS 7.1, 7.2, 7.4 (ACT-16 to 18) | \$1,395 (9h) | \$60 (1.8M tokens) | \$220 | **\$1,675** | \$13,760 | Milestone M3 achieved (Reverse proxy buffering verified) |
| **Wave 5: Integrated Acceptance** | WBS 8.0 (ACT-19) | \$2,670 (18h) | \$35 (1.0M tokens) | \$400 | **\$3,105** | **\$16,865** | Milestone M4 achieved (Autoscaler & reaper verified) |
| **Total Cost Baseline** | **WBS 1.0 through 8.0** | **\$14,290 (90h)** | **\$375 (10.6M)** | **\$2,200** | **\$16,865** | **\$16,865** | Milestone M5 pass (12 Charter benefits proven) |

---

## 2. Reserves and total project budget

| Budget component | Allocation amount | % of Cost Baseline | Release authority | Trigger / governance rule |
|---|:---:|:---:|---|---|
| **Base Work Package Estimates** | **\$14,665** | 87.0% | Project Manager | Planned delivery across 19 activities and 5 waves. |
| **Cost Contingency Reserve** | **\$2,200** | 13.0% | Project Manager | Unforeseen technical tuning, agent repair turns, test retry runs. |
| **Total Cost Baseline** | **\$16,865** | 100.0% | `approve-pmp` | Formal baseline tracked via Earned Value Management (EVM). |
| **Management Reserve** | **\$3,500** | 20.8% | Project Sponsor (Menno) | Unforeseen external host OS patches, Windows licensing changes. |
| **Total Project Budget** | **\$20,365** | 120.8% | Project Sponsor | Within PM delegated authority (\$25,000); no Steering Committee vote needed. |

---

## 3. Budget reconciliation and funding constraints

1. **Authority Headroom**:
   - The total authorized project budget of **\$20,365** leaves **\$4,635** in headroom below the **\$25,000** limit.
2. **Cash Flow and Disbursement**:
   - Contractor payments are staged at wave completion upon passing designated verification gates (`spec_gate.py` $\rightarrow$ tests $\rightarrow$ `pr_gate.py`).
   - AI token expenditure is billed continuously against API quotas ($\approx \$75\text{/week}$).
