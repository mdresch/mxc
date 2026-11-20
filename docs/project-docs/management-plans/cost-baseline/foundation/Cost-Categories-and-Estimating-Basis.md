---
artifact_id: cost-foundation-categories-estimating-basis
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.D-1
pmbok_process: Plan Financial Management
depends_on:
  - 6.D-0P
---

# Cost Categories and Estimating Basis — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Defines measurement rules, cost categories, contractor rate structures, and estimation methods grounded in the Resource Baseline.

## 1. Cost categories and estimation rules

| Cost category | Unit / currency | Included cost elements | Exclusions | Estimating method | Evidence source |
|---|---|---|---|---|---|
| **Contractor Labor: Architecture & Governance** | USD / hour | System Architect (\$180–\$220/hr) and PM/Governance oversight (\$140–\$160/hr). | Full-time administrative overhead. | Parametric / Three-point estimate | [Resource-Capacity-Estimates.md](../../resource-baseline/foundation/Resource-Capacity-Estimates.md) |
| **Contractor Labor: Platform & Security Engineering** | USD / hour | Platform Lead (\$150–\$185/hr) and Security Lead (\$160–\$195/hr) review hours. | Unrelated host hardware repairs. | Parametric / Analogous engineering benchmarks | [Resource-Role-Catalogue.md](../../resource-baseline/foundation/Resource-Role-Catalogue.md) |
| **Contractor Labor: Gateway & SRE Engineering** | USD / hour | Gateway Lead (\$140–\$175/hr), SRE Lead (\$140–\$175/hr), Test Lead (\$110–\$140/hr). | Post-Phase 1 24/7 operations support. | Parametric / Engineering build & test hours | Schedule Activity List WBS 3.0, 7.0, 8.0 |
| **AI Computation / LLM API Quotas** | USD / 1M tokens | Anthropic Claude / Google Gemini API token usage across 208.8 agent turns. | Local open-source models running on host. | Measured consumption benchmark ($\approx \$15\text{/M input}$, $\$75\text{/M output}$) | Agent turn forecasts ($\approx 10.6\text{M}$ tokens $\rightarrow \approx \$350$) |
| **Virtualization Infrastructure & Licensing** | USD / unit | Windows 11 Enterprise volume licenses and host storage expansion. | Existing workstation hardware depreciation. | Market vendor pricing / quotes | Microsoft Volume Licensing quotes |

---

## 2. Assumptions, controls, and approval thresholds

1. **Base Currency**: All cost estimates and rate assignments are expressed in **USD**.
2. **Contractor Rate Indexing**: Hourly rates reflect current market contractor rates for specialized Windows kernel/Hyper-V, systems programming, and PMBOK 8 governance expertise.
3. **Approval Threshold**:
   - The Project Manager holds sole delegated spending authority up to **USD 25,000**.
   - Any contractor engagement or procurement commitment exceeding **USD 25,000** requires formal review and approval by the Steering Committee.
