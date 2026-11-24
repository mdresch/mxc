---
artifact_id: resource-foundation-capacity-estimates
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-2
pmbok_process: Estimate Resources
depends_on:
  - 6.C-1
  - 6.B-7
---

# Resource Capacity Estimates — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Quantifies human staffing effort, contractor hourly billing rate benchmarks, agent reasoning capacities, and physical/virtual infrastructure sizing across Phase 1.

## 1. Human labor demand, capacity, and contractor hourly rate estimates

Human effort focuses on architectural design, code review, gate adjudication, and governance verification rather than raw line-by-line manual coding. The table below includes the designated places for contractor hourly rate benchmarks and total labor cost valuation:

| Human role | Schedule wave commitment | Total estimated demand | Contractor hourly rate range (USD/hr) | Estimated labor valuation range (USD) | Allocation basis | Dedicated capacity |
|---|---|:---:|:---:|:---:|---|:---:|
| **Project Sponsor / PM (Menno)** | Waves 1–5 | **18 hours** | \$140 – \$160 / hr | \$2,520 – \$2,880 | Charter oversight, PMP baseline reviews, gate approvals, status tracking. | Available |
| **Lead / System Architect** | Waves 1, 3, 5 | **12 hours** | \$180 – \$220 / hr | \$2,160 – \$2,640 | Contract schemas, ADR compliance audits, network architecture review. | Available |
| **Platform / Hyper-V Lead** | Waves 1, 2 | **16 hours** | \$150 – \$185 / hr | \$2,400 – \$2,960 | VM configuration review, bake pipeline auditing, hypervisor troubleshooting. | Available |
| **Security Lead** | Waves 1, 2 | **10 hours** | \$160 – \$195 / hr | \$1,600 – \$1,950 | Port ACL policy verification, differencing disk forensic diff audit. | Available |
| **Gateway / Ingress Lead** | Wave 3 | **10 hours** | \$140 – \$175 / hr | \$1,400 – \$1,750 | Reverse proxy socket design review, 503 fallback rule validation. | Available |
| **SRE / Autoscaler Lead** | Wave 4 | **10 hours** | \$140 – \$175 / hr | \$1,400 – \$1,750 | Buffer replenish logic review, reaper timeout thresholds validation. | Available |
| **Test Coordinator** | Waves 2, 4, 5 | **14 hours** | \$110 – \$140 / hr | \$1,540 – \$1,960 | PR gate review triage, end-to-end multi-agent test execution validation. | Available |
| **Total Human Labor** | Waves 1–5 | **90 person-hours** | **Blended: \$145 – \$177 / hr** | **\$13,020 – \$15,890** | Replaces an estimated 480h of manual implementation labor. | Available |

> [!NOTE]
> The total estimated contractor labor valuation of **\$13,020 – \$15,890** is well within the Project Manager's delegated approval threshold of **\$25,000**, requiring no Steering Committee escalation for labor contracting alone.

---

## 2. Autonomous agent reasoning capacity (AI computation demand)

Autonomous agent workers execute code creation, refactoring, unit test authoring, and documentation tasks:

| Work package wave | WBS items | Total agent turns ($T_e$) | Estimated token demand (input/output) | Tool invocations | Concurrency limit |
|---|---|:---:|:---:|:---:|:---:|
| **Wave 1: Base Platform** | WBS 1.0, 2.1, 2.2, 4.1, 6.2 | **49.9 turns** | $\approx 2.4\text{M tokens}$ | $\approx 120\text{ tool calls}$ | Up to 3 parallel workers |
| **Wave 2: State & Image** | WBS 4.2, 5.1, 5.2, 5.3, 6.1, 6.3 | **64.0 turns** | $\approx 3.2\text{M tokens}$ | $\approx 160\text{ tool calls}$ | Up to 3 parallel workers |
| **Wave 3: Ingress Gateway** | WBS 3.1, 3.2, 3.3, 7.3 | **44.3 turns** | $\approx 2.2\text{M tokens}$ | $\approx 110\text{ tool calls}$ | Up to 2 parallel workers |
| **Wave 4: Autoscaling & SRE**| WBS 7.1, 7.2, 7.4 | **34.9 turns** | $\approx 1.8\text{M tokens}$ | $\approx 90\text{ tool calls}$ | Up to 2 parallel workers |
| **Wave 5: Integrated Acceptance**| WBS 8.0 | **15.7 turns** | $\approx 1.0\text{M tokens}$ | $\approx 45\text{ tool calls}$ | 1 test worker |
| **Total AI Demand** | Phase 1 Total | **208.8 turns** | $\approx \mathbf{10.6\text{M tokens}}$ | $\approx \mathbf{525\text{ tool calls}}$ | Swarm / isolated branch workers |

---

## 3. Material infrastructure capacity sizing (host & virtual resources)

Based on approved WBS requirements and ADR-001 through ADR-007:

| Infrastructure dimension | Minimum development capacity | Recommended Phase 1 production target | Sizing basis & calculation |
|---|---|---|---|
| **Host CPU Cores** | 8 physical cores (16 threads) | 16 physical cores (32 threads) | Guest CPU allocation: 2 vCPUs per active VM. Suspended guests consume 0.0% CPU. |
| **Host System RAM** | 32 GB DDR4/DDR5 ECC | 64 GB DDR5 ECC | Active VM: $\approx 2.0\text{GB}$; Suspended standby VM: $\le 700\text{MB}$ commit; Host OS reserve: $8.0\text{GB}$. Capacity supports 10–20 standby VMs simultaneously. |
| **Host NVMe Storage** | 500 GB NVMe PCIe Gen 4 | 1.0 TB NVMe PCIe Gen 4 | Golden Base VHDX: $\approx 25\text{GB}$; Differencing `.avhdx` per session: $\approx 2.0\text{GB}$ max; Swap/temp storage: $50\text{GB}$. |
| **Host Storage Throughput** | $\ge 2,500\text{ MB/s}$ read | $\ge 5,000\text{ MB/s}$ sequential read, $\ge 500\text{K IOPS}$ | Critical for meeting sub-300ms `Resume-VM` and instant differencing disk fork. |
| **Virtual Networking** | 1 GbE dedicated virtual switch | 10 GbE internal switch with Port ACLs | Sub-millisecond packet traversal between reverse proxy and guest endpoints. |
| **Guest OS Licenses** | 5 Windows 11 Enterprise evaluation / volume | 20 Windows 11 Enterprise volume licenses | Supports dynamic warm buffer pool ($K_{\text{base}} = 2$, $K_{\text{max}} = 10$) and active running sessions. |
