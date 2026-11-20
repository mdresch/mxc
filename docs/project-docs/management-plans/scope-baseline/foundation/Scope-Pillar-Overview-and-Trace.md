---
artifact_id: scope-foundation-pillar-overview-trace
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.A-0P
depends_on: []
---

# Scope Pillar Overview and Trace — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft — Ready for Review. Full traceability from the 6 Topic Pillars and approved initiating inputs (Charter and Benefits Statement) to WBS deliverables and verification milestones.

## 1. Strategic pillar and scope deliverable mapping

| Topic Pillar | Strategic objective | Scope deliverable | Decomposed WBS packages | Approved requirements & stories | Acceptance milestone |
|---|---|---|---|---|:---:|
| **—** | Governance & Planning Integrity | Governance baseline & traceability pack | **WBS 1.0** | Project Charter; Benefits Statement; PMP | Gate 6.A-0 / M1 Entry |
| **TP-01 Isolation** | Hardware-level VM boundary & full Windows subsystems | Isolated Hyper-V Gen 2 Guest | **WBS 2.1, 2.2** | BRD-001; ADR-001; Stories 1.1, 1.2 | Milestone M1 |
| **TP-02 Ingress** | Zero-cold-start illusion via connection buffering | Connection-Buffering Ingress & Router | **WBS 3.1, 3.2, 3.3** | BRD-002; ADR-002; Stories 2.1, 2.2, 2.3 | Milestone M3 |
| **TP-03 Image supply** | Clean production image & warm checkpoint | Production VHDX & Checkpoint Pipeline | **WBS 4.1, 4.2** | BRD-003; ADR-003; Stories 3.1, 3.2 | Milestone M1 |
| **TP-04 Paused footprint** | Zero idle CPU/GPU, trimmed RAM, sub-300ms resume | Standby Resource Management | **WBS 5.1, 5.2, 5.3** | BRD-004; ADR-004; Stories 4.1, 4.2, 4.3 | Milestone M2 |
| **TP-05 Session sterility** | Ephemeral differencing disk & network airgap | Session Lifecycle & Egress Control | **WBS 6.1, 6.2, 6.3, 6.4** | BRD-005; ADR-005; Stories 5.1, 5.2, 5.3 | Milestone M2 |
| **TP-06 Pool & wake hygiene** | Sub-second replenishment, surge scale, reaper | Dynamic Pool Manager & Reaper | **WBS 7.1, 7.2, 7.3, 7.4** | BRD-006; ADR-006; Stories 6.1, 6.2, 6.3, 6.4 | Milestone M4 |
| **—** | Integrated Capability Demonstration | Phase 1 Integrated Acceptance Gate | **WBS 8.0** | 12 Charter Benefits; USER_STORIES.md | Milestone M5 |

---

## 2. Trace to scope bands and execution milestones

| Milestone | Schedule target | Included WBS packages | Verifying deliverables | Critical acceptance criteria |
|---|:---:|---|---|---|
| **M1** | $T_0 + 11.0\text{h}$ | WBS 1.0, 2.1, 2.2, 4.1, 4.2, 6.2 | VM provisioner, bake script, snapshot | Gen 2 UEFI verified; image free of dev tools; baseline checkpoint ready |
| **M2** | $T_0 + 15.8\text{h}$ | WBS 5.1, 5.2, 5.3, 6.1, 6.3 | Suspend monitor, RAM trimmer, diff disk | PerfMon 0.0% CPU/GPU; RAM $\le 700\text{MB}$; resume $\le 300\text{ms}$; parent hash match |
| **M3** | $T_0 + 19.5\text{h}$ | WBS 3.1, 3.2, 3.3, 7.3 | Ingress proxy, router rules, PRNG reset | TTFB $\le 800\text{ms}$; 0 wake 502/504s; dual routing verified |
| **M4** | $T_0 + 26.8\text{h}$ | WBS 7.1, 7.2, 7.4 | Buffer daemon, autoscaler, fleet reaper | Replenish $\approx 1.5\text{s}$; burst surge to $K_{\text{max}}$; idle deallocation verified |
| **M5** | $T_0 + 31.0\text{h}$ | WBS 8.0 | End-to-end integration test harness | Automated pass of all 12 operational benefits from Benefits Statement |

---

## 3. Review checks and reconciliation status

- **Check 1: Initiating Inputs Reconciled**: Both [Project Charter](../../Project-Charter.md) and [Benefits Statement](../../Benefits-Statement.md) are approved.
- **Check 2: Requirements Traceability**: All 17 User Stories (Stories 1.1–6.4) and BRD-001–006 are 100% mapped to WBS 2.1–7.4 without orphan requirements.
- **Check 3: No Unfunded or Unbounded Scope**: Exclusions explicitly documented; budget and schedule bounds aligned.
