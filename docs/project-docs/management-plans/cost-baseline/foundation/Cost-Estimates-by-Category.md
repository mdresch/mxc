---
artifact_id: cost-foundation-estimates-by-category
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.D-2
pmbok_process: Estimate Costs
depends_on:
  - 6.D-1
  - 6.B-7
  - 6.C-7
---

# Cost Estimates by Category — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Quantifies cost estimates per WBS package by reconciling Schedule duration forecasts, Resource labor hours, and contractor hourly rate assignments.

## 1. WBS cost estimates by category and contractor rates

| WBS ID | Work package description | Cost category | Quantity / rate | Estimate range (USD) | Basis / source | Confidence | Owner |
|---|---|---|---|:---:|---|:---:|---|
| **1.0** | Scope & Baseline Reconciliation | Governance Contractor | 8h @ \$150/hr | \$1,100 – \$1,300 | PMP alignment hours | High | Menno Drescher |
| **2.1** | Gen 2 VM Provisioning | Platform Contractor | 8h @ \$165/hr | \$1,200 – \$1,450 | Hyper-V automation review | High | Platform Lead |
| **2.2** | In-Guest Subsystems Validation | Platform Contractor | 4h @ \$165/hr | \$600 – \$750 | Guest WMI probe review | Medium | Platform Lead |
| **3.1** | Ingress Connection Buffering | Gateway Contractor | 6h @ \$155/hr | \$850 – \$1,050 | Reverse proxy socket review | Medium | Gateway Lead |
| **3.2** | Ingress Saturation & Fallback | Gateway Contractor | 2h @ \$155/hr | \$280 – \$350 | 503 fallback rule audit | High | Gateway Lead |
| **3.3** | Path & Port Dual Routing | Gateway Contractor | 2h @ \$155/hr | \$280 – \$350 | Route dispatcher tests | High | Gateway Lead |
| **4.1** | Clean Production VHDX Bake | Release Contractor | 6h @ \$165/hr | \$900 – \$1,100 | Image bake script audit | High | Release Lead |
| **4.2** | Warm Baseline Checkpoint | Release Contractor | 4h @ \$165/hr | \$600 – \$750 | Checkpoint snapshot test | High | Release Lead |
| **5.1** | Zero Idle CPU/GPU Suspend | Platform Contractor | 3h @ \$165/hr | \$450 – \$550 | PerfMon counter audit | High | Platform Lead |
| **5.2** | RAM Pre-Trimming Optimization | Platform Contractor | 3h @ \$165/hr | \$450 – \$550 | Memory trimmer review | Medium | Platform Lead |
| **5.3** | Sub-300ms Resume Latency | Platform Contractor | 4h @ \$165/hr | \$600 – \$750 | Resume stopwatch benchmarks | Medium | Platform Lead |
| **6.1** | Ephemeral Differencing Disk | Security Contractor | 4h @ \$175/hr | \$650 – \$800 | Differencing disk teardown audit | High | Security Lead |
| **6.2** | Network Airgap Port ACLs | Security Contractor | 4h @ \$175/hr | \$650 – \$800 | Port ACL verification | High | Security Lead |
| **6.3** | Discard & Reproduce Path | Security Contractor | 2h @ \$175/hr | \$320 – \$400 | Forensics diff audit | High | Security Lead |
| **7.1** | Instant Buffer Replenishment | SRE Contractor | 4h @ \$155/hr | \$580 – \$700 | Replenish loop review | High | SRE Lead |
| **7.2** | Concurrency Surge Scale | SRE Contractor | 3h @ \$155/hr | \$430 – \$530 | Autoscaler burst test review | Medium | SRE Lead |
| **7.3** | In-Guest Wake Hygiene | SRE Contractor | 3h @ \$155/hr | \$430 – \$530 | PRNG / clock unpause review | Medium | SRE Lead |
| **7.4** | Idle Fleet Reaper & Reclaim | SRE Contractor | 3h @ \$155/hr | \$430 – \$530 | Reaper idle timeout audit | High | SRE Lead |
| **8.0** | Integrated Phase 1 Acceptance | Test Coordinator / Architect | 18h @ \$160/hr | \$2,600 – \$3,150 | Multi-session E2E pass & PR gate | High | Test Coordinator |
| **—** | AI Reasoning Tokens (All WBS) | Cloud LLM Compute | 10.6M tokens | \$300 – \$450 | Agent reasoning turns ($208.8\text{ turns}$) | High | Dev Coordinator |
| **Total** | **Phase 1 Execution Baseline** | **Blended** | **90h Labor + AI** | **\$13,460 – \$16,790** | Reconciled with Schedule & Resource | High | Menno Drescher |

---

## 2. Cost reconciliation and funding limits

1. **Reconciliation to Scope and Schedule**:
   - The total estimated demand of **90 contractor hours** corresponds exactly to the 90 human hours modeled across Waves 1–5 in [Resource-Capacity-Estimates.md](../../resource-baseline/foundation/Resource-Capacity-Estimates.md).
   - The blended contractor labor cost of **\$13,020 – \$15,890** plus **\$300 – \$450** in AI token costs totals **\$13,460 – \$16,790**.
2. **Steering Committee Approval Threshold**:
   - Total base cost **\$16,790 (max)** leaves **\$8,210** in unallocated headroom before reaching the **USD 25,000** Project Manager threshold, providing ample buffer for contingency drawdown without requiring Steering Committee escalation.
