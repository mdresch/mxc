---
artifact_id: resource-foundation-pillar-overview-trace
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-0P
depends_on:
  - 6.A-7
  - 6.B-7
---

# Resource Pillar Overview and Trace — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Traces resource requirements (human expertise, agent worker roles, and material infrastructure) to the 6 Topic Pillars.

## 1. Topic pillar resource mapping

| Topic Pillar | Strategic outcome | Material resource requirements | Human role required | Agent worker role | Schedule window |
|---|---|---|---|---|:---:|
| **TP-01 Isolation** | Hyper-V Gen 2 VM boundary & full Windows guest fidelity | Windows 11 / Server Hyper-V host, UEFI firmware, virtual TPM, 2 vCPUs/guest. | Platform Lead | Platform Worker | Wave 1 (M1) |
| **TP-02 Ingress** | Zero-cold-start illusion via HTTP socket hold ($\le 800\text{ms}$ TTFB) | Reverse proxy listener, loopback virtual network adapter, TCP socket buffers. | Gateway Lead | Gateway Worker, DevOps Worker | Wave 3 (M3) |
| **TP-03 Image supply** | Immutable clean production VHDX and instant warm checkpoint | 25 GB Golden Master VHDX storage, NVMe $\ge 2.5\text{GB/s}$, DISM image capture. | Release Lead | Release Worker | Waves 1–2 (M1) |
| **TP-04 Paused footprint** | Zero idle CPU/GPU consumption, trimmed RAM ($\le 700\text{MB}$), sub-300ms resume | High-speed host RAM, PerfMon telemetry counters, Hyper-V memory management APIs. | Platform Lead | Platform Worker | Wave 2 (M2) |
| **TP-05 Session sterility** | Disposable VM lifecycle with differencing disk detachment | Ephemeral `.avhdx` differencing disks, Hyper-V vSwitch Port ACLs, SHA-256 diff tools. | Security Lead | Security Worker | Waves 1–2 (M2) |
| **TP-06 Pool & wake hygiene** | Sub-second buffer replenishment, dynamic surge, PRNG/clock reset, reaper | Background worker thread, host clock synchronization, guest `RDRAND`, reaper timer. | SRE Lead | SRE Worker | Waves 3–4 (M4) |
| **Cross-Cutting Governance** | PMBOK 8 / SIDPA lifecycle conformance and acceptance validation | Python 3.11 test runner, `pytest`, git repository, Claude/Gemini API quota. | Project Manager, Test Coordinator | Coordinator Agent, Test Coordinator | Waves 1–5 (M5) |

---

## 2. Resource trace findings and critical constraints

1. **NVMe Read/Write Throughput Constraint**:
   - TP-03 and TP-04 depend on NVMe PCIe Gen 4 storage ($\ge 2,500\text{ MB/s}$) to guarantee sub-300ms `Resume-VM` times from warm checkpoints.
2. **Host Memory Sizing Constraint**:
   - TP-04 requires strict pre-trimming to ensure suspended VMs do not exceed 700 MB each, enabling a 10-VM standby pool within $\approx 7\text{GB}$ host RAM.
3. **Dual Role Governance Constraint**:
   - Project Sponsor and Project Manager roles are both held by Menno Drescher; steering committee oversight ensures segregation of duties for capital allocations $> \$25,000$.
