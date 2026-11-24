---
artifact_id: schedule-foundation-pillar-overview-trace
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-0P
depends_on:
  - scope-management
---

# Schedule Pillar Overview and Trace — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Traces the 6 Topic Pillars (TP-01 through TP-06) and strategic outcomes into WBS work packages, schedule activities, and milestone gates.

## 1. Strategic pillar trace matrix

| Topic Pillar | Strategic outcome | Scope / WBS reference | Activity ID | Target milestone | Verification evidence source | Schedule implication |
|---|---|---|---|:---:|---|---|
| **—** | Governance & Planning Integrity | WBS 1.0 | ACT-01 | Gate 6.B-0 | `scripts/validate_lifecycle.py`, PMP Manifest | Unlocks execution authorization for all waves. |
| **TP-01 Isolation** | Hyper-V Gen 2 boundary & full Windows guest fidelity | WBS 2.1, WBS 2.2 | ACT-02, ACT-03 | Milestone M1 | `Get-VM`, WMI, COM+ probe suite | Critical root dependency; hardware virtualization prerequisite. |
| **TP-02 Ingress** | Zero-cold-start illusion via HTTP socket hold ($\le 800\text{ms}$ TTFB) | WBS 3.1, WBS 3.2, WBS 3.3 | ACT-12, ACT-13, ACT-14 | Milestone M3 | Reverse proxy latency benchmarks, 503 fallback load test | Critical path centerpiece connecting paused state to users. |
| **TP-03 Image supply** | Immutable clean production VHDX and instant warm checkpoint | WBS 4.1, WBS 4.2 | ACT-04, ACT-05 | Milestone M1 | Automated image bake logs, checkpoint snapshot validation | Critical path gate defining the golden base for all clones. |
| **TP-04 Paused footprint** | Zero idle CPU/GPU consumption, trimmed RAM, sub-300ms resume | WBS 5.1, WBS 5.2, WBS 5.3 | ACT-07, ACT-08, ACT-09 | Milestone M2 | PerfMon CPU/GPU 0.0% counter, `Resume-VM` stopwatch | Enables high-density standby without resource waste. |
| **TP-05 Session sterility** | Single-session disposable VM lifecycle with bit-identical base | WBS 6.1, WBS 6.2, WBS 6.3, WBS 6.4 | ACT-06, ACT-10, ACT-11 | Milestone M2 | Differencing `.avhdx` deletion probe, Port ACL unit tests | Guarantees zero cross-session data leakage or tampering. |
| **TP-06 Pool & wake hygiene** | Sub-second buffer replenishment, surge scale, PRNG/clock reset, reaper | WBS 7.1, WBS 7.2, WBS 7.3, WBS 7.4 | ACT-15, ACT-16, ACT-17, ACT-18 | Milestone M4 | Velocity autoscaler logs, in-guest `RDRAND`/clock test, reaper log | Maintains warm capacity under variable burst loads. |
| **—** | Integrated Phase 1 Capability Demonstration | WBS 8.0 | ACT-19 | Milestone M5 | End-to-end multi-session test harness | Final project milestone unblocking Phase 2 production rollout. |

---

## 2. Milestone gate alignment

1. **Gate 6.B-0 (Planning Gate)**: Complete reconciliation between Scope WBS, Requirements Traceability, and Schedule Network.
2. **Milestone M1 (Base Platform & Image)**: Gen 2 VM automation and clean production VHDX image established; initial warm checkpoint captured.
3. **Milestone M2 (Standby State & Sterility)**: Host CPU/GPU quiescence verified; ephemeral differencing disks detach cleanly.
4. **Milestone M3 (Ingress Protocol Router)**: Connection-buffering reverse proxy connects incoming HTTP requests to warm VMs under 800ms.
5. **Milestone M4 (Autoscaling & SRE Reaper)**: Dynamic buffer replenishment and scale-down reaper verified under burst concurrency.
6. **Milestone M5 (Phase 1 Acceptance)**: Comprehensive acceptance demonstration satisfying all 12 Project Charter benefits.
