---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "12.1 Procurement Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Business-Case.md"
  - "resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md"
process: "Define procurement needs, make-or-buy analysis, contract mechanisms, and approval controls"
outputs:
  - "Procurement-Management-Plan.md"
status: "Approved"
---

# Procurement Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the make-or-buy analysis, contract structures, vendor management policies, and procurement spending limits.

## 1. Procurement approach and make-or-buy analysis

MXC Phase 1 is designed to maximize in-house engineering and autonomous agent delivery while leveraging existing enterprise virtualization infrastructure, minimizing external procurement:

| Deliverable / capability | Make or buy decision | Rationale & approach | Sourcing method |
|---|:---:|---|---|
| **Hyper-V VM Provisioning & Automation** | **MAKE** | In-house PowerShell 7+ scripts leveraging native Windows Hyper-V APIs. | Platform Lead & Agent Workers |
| **VHDX Image Bake & Checkpoint Pipeline** | **MAKE** | Custom headless baking scripts and DISM sysprep automation. | Release Lead & Agent Workers |
| **Connection-Buffering Ingress Proxy** | **MAKE** | Lightweight in-house reverse proxy tailored for HTTP socket holding and pool leasing. | Gateway Lead & Agent Workers |
| **Fleet Autoscaler & Reaper Daemon** | **MAKE** | Custom background services managing pool replenishment and idle reclamation. | SRE Lead & Agent Workers |
| **In-Guest IPC Binary (`wxc-exec`)** | **MAKE** | Project-specific zero-network binary utilizing Hyper-V KVP data exchange. | Gateway / SRE Leads |
| **Host Virtualization Hardware** | **REUSE** | Existing dedicated Windows 11 Enterprise workstation with AMD-V/SLAT and NVMe SSD. | Internal existing asset |
| **AI LLM Reasoning Quotas** | **ACQUIRE** | Cloud API tokens (Claude 3.5 Sonnet / Gemini 1.5 Pro) for autonomous agent workers. | Operating expense ($\approx \$375$ for 10.6M tokens) |
| **Windows OS Licenses** | **ACQUIRE** | Windows 11 Enterprise volume licensing / evaluation media for golden bake. | Existing Microsoft Volume Licensing |
| **Specialized Contractor Labor** | **CONTRACT** | Part-time specialized advisory and review capacity (90 person-hours across 7 roles). | Time & Materials contractor agreements (\$145–\$177/hr) |

---

## 2. Contractor procurement and statement of work controls

1. **Contract Type**:
   - Human engineering leads operate under flexible **Time and Materials (T&M)** contractor engagements capped at 90 total person-hours across Phase 1.
2. **Contractor Rate Caps**:
   - Hourly contractor rates are capped strictly by role per [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md) (e.g. Lead Architect $\le \$220\text{/hr}$, Platform Lead $\le \$185\text{/hr}$, Test Coordinator $\le \$140\text{/hr}$).
3. **Deliverable-Based Invoicing**:
   - Invoicing is verified against milestone gate pass records (`spec_gate.py` $\rightarrow$ `pr_gate.py` $\rightarrow$ milestone completion).

---

## 3. Authority limits and procurement governance

1. **Project Manager Spending Authority**:
   - The Project Manager holds delegated procurement authority up to **USD 25,000**.
   - Total planned Phase 1 procurement (Contractor labor \$14,290 + AI compute \$375 + Contingency \$2,200 = **\$16,865**) is well within this delegated threshold.
2. **Steering Committee Escalation**:
   - Any single procurement commitment, vendor contract, or capital asset acquisition exceeding **USD 25,000** requires formal review and independent approval by the Steering Committee.
3. **Procurement Records Retention**:
   - All contractor statements of work, rate agreements, timesheet logs, and AI API billing records are maintained in `docs/registers/` for auditability.
