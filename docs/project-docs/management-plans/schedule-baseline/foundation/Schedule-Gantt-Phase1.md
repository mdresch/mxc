---
artifact_id: schedule-foundation-gantt
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-2B
pmbok_process: Develop Schedule — develop schedule model
depends_on:
  - 6.B-2
  - 6.B-2A
  - 6.B-4
---

# Schedule Model / Gantt — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Reconciles the Activity List and Network into an Asynchronous Execution Wave Model with Early/Late schedules, Float, and Milestone Gates.

## 1. Activity schedule model (hours from project execution start $T_0$)

| Activity ID | Activity name | Duration ($T_e$) | Early Start (ES) | Early Finish (EF) | Late Start (LS) | Late Finish (LF) | Total Float (TF) | Free Float (FF) | Milestone / Gate |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **ACT-01** | Scope & WBS Reconciliation | 1.1h | 0.0h | 1.1h | 0.0h | 1.1h | 0.0h | 0.0h | Gate 6.B-0 |
| **ACT-02** | Gen 2 VM Provisioning | 2.6h | 1.1h | 3.7h | 1.1h | 3.7h | 0.0h | 0.0h | M1 Entry |
| **ACT-03** | In-Guest Subsystems Validation | 2.1h | 3.7h | 5.8h | 5.8h | 7.9h | 2.1h | 2.1h | — |
| **ACT-04** | Clean Production VHDX Bake | 4.2h | 3.7h | 7.9h | 3.7h | 7.9h | 0.0h | 0.0h | — |
| **ACT-06** | Network Airgap & Port ACLs | 2.1h | 3.7h | 5.8h | 24.7h | 26.8h | 21.0h | 21.0h | — |
| **ACT-05** | Warm Checkpoint Capture | 3.1h | 7.9h | 11.0h | 7.9h | 11.0h | 0.0h | 0.0h | **Milestone M1** |
| **ACT-07** | Zero Idle CPU & GPU Suspension | 2.1h | 11.0h | 13.1h | 11.0h | 13.1h | 0.0h | 0.0h | — |
| **ACT-08** | Memory Working Set Pre-Trimming | 2.2h | 13.1h | 15.3h | 24.6h | 26.8h | 11.5h | 11.5h | — |
| **ACT-09** | Sub-300ms Resume-VM Latency | 2.7h | 13.1h | 15.8h | 13.1h | 15.8h | 0.0h | 0.0h | — |
| **ACT-10** | Ephemeral Differencing Disk | 2.1h | 11.0h | 13.1h | 13.7h | 15.8h | 2.7h | 2.7h | — |
| **ACT-11** | Discard & Reproduce Verification | 2.1h | 13.1h | 15.2h | 24.7h | 26.8h | 11.6h | 11.6h | **Milestone M2** |
| **ACT-15** | In-Guest Wake Hygiene & PRNG | 2.1h | 15.8h | 17.9h | 24.7h | 26.8h | 8.9h | 8.9h | — |
| **ACT-12** | Ingress Buffering & Hold | 3.7h | 15.8h | 19.5h | 15.8h | 19.5h | 0.0h | 0.0h | **Milestone M3** |
| **ACT-13** | Ingress Saturation & 503 Fallback | 2.1h | 19.5h | 21.6h | 24.7h | 26.8h | 5.2h | 5.2h | — |
| **ACT-14** | Path & Port Dual Routing | 1.7h | 19.5h | 21.2h | 25.1h | 26.8h | 5.6h | 5.6h | — |
| **ACT-16** | Instant Buffer Replenish | 2.6h | 19.5h | 22.1h | 19.5h | 22.1h | 0.0h | 0.0h | — |
| **ACT-17** | Concurrency Surge Expansion | 2.6h | 22.1h | 24.7h | 22.1h | 24.7h | 0.0h | 0.0h | — |
| **ACT-18** | Fleet Reaper & Reclamation | 2.1h | 24.7h | 26.8h | 24.7h | 26.8h | 0.0h | 0.0h | **Milestone M4** |
| **ACT-19** | Phase 1 Acceptance Gate | 4.2h | 26.8h | 31.0h | 26.8h | 31.0h | 0.0h | 0.0h | **Milestone M5** |

---

## 2. Milestone schedule and verification events

| Milestone | Title | Schedule Time ($T_0 + H$) | Deliverables required | Verifying gate / script |
|---|---|:---:|---|---|
| **M1** | VM Platform & Warm Checkpoint Ready | **11.0h** | ACT-01, ACT-02, ACT-03, ACT-04, ACT-05 | `scripts/spec_gate.py` + Checkpoint file integrity |
| **M2** | Standby Sterility & Storage Verified | **15.8h** | ACT-07, ACT-08, ACT-09, ACT-10, ACT-11 | PerfMon 0.0% counter + .avhdx hash isolation test |
| **M3** | Ingress Gateway & Buffering Live | **19.5h** | ACT-12 | Gateway HTTP proxy proxying to unpaused VM $\le 800\text{ms}$ |
| **M4** | Fleet Autoscaling & Reaper Operational | **26.8h** | ACT-13, ACT-14, ACT-15, ACT-16, ACT-17, ACT-18 | Burst load stress test + 180s/300s reaper verification |
| **M5** | Phase 1 Final Integrated Acceptance | **31.0h** | ACT-19 (All 17 stories) | Full operational pass of 12 strategic benefits (`pr_gate.py`) |

---

## 3. Wave execution model for asynchronous agents

```mermaid
gantt
    title MXC Phase 1 Asynchronous Agent Schedule Baseline
    dateFormat X
    axisFormat %s h

    section Wave 1: Base Platform
    ACT-01 Scope Reconciliation        :crit, 0, 1.1
    ACT-02 Gen 2 VM Provisioning       :crit, 1.1, 3.7
    ACT-03 In-Guest Windows Subsystems :active, 3.7, 5.8
    ACT-04 Clean VHDX Bake             :crit, 3.7, 7.9
    ACT-06 Network Airgap & ACLs       :active, 3.7, 5.8

    section Wave 2: Paused State & Image
    ACT-05 Warm Baseline Checkpoint    :crit, 7.9, 11.0
    ACT-07 Zero CPU/GPU Suspension     :crit, 11.0, 13.1
    ACT-08 Memory Pre-Trimming         :active, 13.1, 15.3
    ACT-09 Sub-300ms Resume            :crit, 13.1, 15.8
    ACT-10 Ephemeral Differencing Disk :active, 11.0, 13.1
    ACT-11 Discard & Reproduce Path    :active, 13.1, 15.2

    section Wave 3: Ingress & Wake
    ACT-12 Ingress Buffering & Hold    :crit, 15.8, 19.5
    ACT-13 Saturation 503 Fallback     :active, 19.5, 21.6
    ACT-14 Path & Port Dual Routing    :active, 19.5, 21.2
    ACT-15 In-Guest Wake Hygiene       :active, 15.8, 17.9

    section Wave 4: Autoscaling & SRE
    ACT-16 Buffer Replenish            :crit, 19.5, 22.1
    ACT-17 Concurrency Surge Scale     :crit, 22.1, 24.7
    ACT-18 Fleet Reaper & Reclaim      :crit, 24.7, 26.8

    section Wave 5: Final Acceptance
    ACT-19 Phase 1 E2E Acceptance      :crit, 26.8, 31.0
```
