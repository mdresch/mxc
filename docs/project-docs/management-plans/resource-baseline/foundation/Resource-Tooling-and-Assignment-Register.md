---
artifact_id: resource-foundation-tooling-assignment-register
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-3
pmbok_process: Acquire Resources
depends_on:
  - 6.C-2
---

# Resource Tooling and Assignment Register — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Comprehensive register of physical hardware, virtualization software, developer tooling, and test infrastructure.

## 1. Tooling and environment inventory

| Resource / tool | Category | WBS use | Assignment / owner | Availability & lead time | License / access constraint |
|---|---|---|---|---|---|
| **Development Host Machine** | Physical Hardware | All | Platform Lead / PM | Immediate (existing workstation) | Windows 11 Enterprise host with BIOS AMD-V/VT-x and SLAT enabled |
| **Hyper-V Hypervisor Role** | Virtualization Stack | 2.1, 4.2, 5.1, 5.3, 6.2 | Platform Lead | Immediate | Windows built-in feature; requires administrative PowerShell privileges |
| **Windows 11 Base ISO / Media** | Operating System Image | 4.1 | Release Lead | Immediate | Valid Windows 11 Enterprise x64 ISO for clean sysprep bake |
| **PowerShell 7.4+ (Core)** | Scripting Engine | 2.1, 4.1, 6.1, 7.1, 7.4 | Platform Lead | Immediate | Open source (MIT); installed on host |
| **Python 3.11+ Environment** | Test & Gate Runtime | 1.0, 8.0, All gates | Quality Coordinator | Immediate | Python 3.11 with `pytest`, `pathlib`, `json` libraries |
| **`wxc-exec` Executable Tool** | Guest Communication | 2.2, 7.3 | Gateway / SRE Lead | Immediate | Project custom binary for zero-network guest IPC via Hyper-V KVP sockets |
| **Ingress HTTP Reverse Proxy** | Networking Software | 3.1, 3.2, 3.3 | Gateway Lead | Immediate (script authoring in Wave 3) | Python/Node lightweight proxy for HTTP socket hold and pool leasing |
| **`spec_gate.py` Tool** | Governance Script | Pre-implementation (All) | Dev Coordinator | Immediate (integrated from SIDPA template) | Local repository script in `scripts/spec_gate.py` |
| **`pr_gate.py` Tool** | Governance Script | Post-implementation (All) | Dev Coordinator | Immediate (integrated from SIDPA template) | Local repository script in `scripts/pr_gate.py` |
| **`validate_lifecycle.py` Tool** | Governance Script | 1.0, 8.0 | Project Manager | Immediate | Local repository script in `scripts/validate_lifecycle.py` |
| **AI LLM Reasoning Environment** | AI Agent Cloud Service | All Agent Workers | Dev Coordinator | Immediate | Anthropic Claude 3.5 Sonnet / Google Gemini 1.5 Pro API quotas |
| **Git & GitHub Repository** | Version Control & CI/CD | All | PM / Dev Coordinator | Immediate | Branch `feat/hyperv-v2-rebased` at `origin` |

---

## 2. Gaps, acquisitions, and environmental setup

1. **Host Execution Permissions**:
   - Hyper-V cmdlets (`New-VM`, `Suspend-VM`, `Resume-VM`, `Add-VMNetworkAdapterAcl`) require elevated Administrator privileges on the Windows host.
   - For sandboxed agent execution, operations modifying `.git` or calling system hypervisor cmdlets use appropriate bypass or host harness runners (`run_command`).
2. **KVP Guest Integration**:
   - Hyper-V Data Exchange Service (KVP) must be enabled within the guest VM integration services to allow host-guest status signaling without opening TCP ports.
3. **Storage Allocation**:
   - Host drive requires at least 150 GB unfragmented NVMe storage dedicated to `C:\Hyper-V\MXC-Pool\` to support simultaneous warm differencing disks.
