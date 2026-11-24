---
artifact_id: schedule-foundation-wbs-forecast
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-4
depends_on:
  - 6.B-1
  - scope-management
---

# WBS Duration Forecast — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Duration forecasts tailored for autonomous agent execution (agent prompt/tool turns and elapsed clock hours).

## 1. Work package duration forecast table

Durations are calculated using three-point PERT estimation:

$$T_e = \frac{O + 4M + P}{6}, \quad \sigma = \frac{P - O}{6}$$

Where:
- **Turns ($T$)**: Autonomous agent reasoning/tool invocations required to complete the story.
- **Clock ($H$)**: Wall-clock hours including test suite execution, VM bake cycles, and gate checks.

| WBS ID | Activity ID | Work package description | Optimistic ($O$) | Most Likely ($M$) | Pessimistic ($P$) | Expected ($T_e$) | Confidence | Source / benchmark | Critical Path |
|---|---|---|---|---|---|---|---|---|:---:|
| **1.0** | ACT-01 | Scope & WBS Baseline Reconciliation | 3 turns / 0.5h | 5 turns / 1.0h | 10 turns / 2.0h | **5.5 turns / 1.1h** | High | Stage 6 scope artifacts audit | No |
| **2.1** | ACT-02 | Gen 2 VM Provisioning (Story 1.1) | 8 turns / 1.5h | 12 turns / 2.5h | 20 turns / 4.0h | **12.7 turns / 2.6h** | High | PowerShell Hyper-V cmdlets benchmark | **Yes** |
| **2.2** | ACT-03 | In-Guest Subsystems Validation (Story 1.2) | 6 turns / 1.0h | 10 turns / 2.0h | 16 turns / 3.5h | **10.3 turns / 2.1h** | Medium | Guest WMI / COM+ probe suite | No |
| **3.1** | ACT-12 | Connection-Buffering Ingress & Hold (Story 2.1) | 10 turns / 2.0h | 15 turns / 3.5h | 25 turns / 6.0h | **15.8 turns / 3.7h** | Medium | Reverse proxy socket buffering prototype | **Yes** |
| **3.2** | ACT-13 | Ingress Saturation & 503 Fallback (Story 2.2) | 6 turns / 1.0h | 9 turns / 2.0h | 15 turns / 3.5h | **9.5 turns / 2.1h** | High | HTTP reverse proxy status handler | No |
| **3.3** | ACT-14 | Path & Port Dual Routing Rules (Story 2.3) | 6 turns / 1.0h | 8 turns / 1.5h | 14 turns / 3.0h | **8.7 turns / 1.7h** | High | Regex route dispatcher tests | No |
| **4.1** | ACT-04 | Clean Production VHDX Bake (Story 3.1) | 8 turns / 2.0h | 12 turns / 4.0h | 20 turns / 7.0h | **12.7 turns / 4.2h** | High | Windows image bake runner script | **Yes** |
| **4.2** | ACT-05 | Warm Baseline Checkpoint Capture (Story 3.2) | 8 turns / 1.5h | 12 turns / 3.0h | 18 turns / 5.0h | **12.3 turns / 3.1h** | High | VM snapshot & RAM serialization test | **Yes** |
| **5.1** | ACT-07 | Zero Idle CPU & GPU Suspension (Story 4.1) | 5 turns / 1.0h | 8 turns / 2.0h | 14 turns / 3.5h | **8.5 turns / 2.1h** | High | PerfMon counter collector tests | **Yes** |
| **5.2** | ACT-08 | Memory Working Set Pre-Trimming (Story 4.2) | 6 turns / 1.0h | 10 turns / 2.0h | 18 turns / 4.0h | **10.7 turns / 2.2h** | Medium | Hyper-V memory management APIs | No |
| **5.3** | ACT-09 | Sub-300ms Resume-VM Latency (Story 4.3) | 8 turns / 1.5h | 12 turns / 2.5h | 20 turns / 4.5h | **12.7 turns / 2.7h** | Medium | `Resume-VM` timing benchmark logs | **Yes** |
| **6.1** | ACT-10 | Ephemeral Differencing Disk (Story 5.1) | 6 turns / 1.0h | 10 turns / 2.0h | 16 turns / 3.5h | **10.3 turns / 2.1h** | High | Differencing VHDX attach/detach loop | No |
| **6.2** | ACT-06 | Network Airgap & Egress Whitelist (Story 5.2) | 6 turns / 1.0h | 8 turns / 2.0h | 14 turns / 3.5h | **8.7 turns / 2.1h** | High | Hyper-V Port ACL rule tests | No |
| **6.3** | ACT-11 | Discard & Reproduce Verification (Story 5.3) | 6 turns / 1.0h | 9 turns / 2.0h | 16 turns / 3.5h | **9.7 turns / 2.1h** | High | Forensic disk diff and replay harness | No |
| **6.4** | — | Session Sterility Assurance (Cross-cutting) | 3 turns / 0.5h | 5 turns / 1.0h | 8 turns / 2.0h | **5.2 turns / 1.1h** | High | Aggregated disk/network clean audit | No |
| **7.1** | ACT-16 | Instant Buffer Replenish (Story 6.1) | 8 turns / 1.5h | 12 turns / 2.5h | 18 turns / 4.0h | **12.3 turns / 2.6h** | High | Background pool worker daemon | **Yes** |
| **7.2** | ACT-17 | Concurrency Surge Dynamic Expansion (Story 6.2) | 8 turns / 1.5h | 12 turns / 2.5h | 18 turns / 4.0h | **12.3 turns / 2.6h** | Medium | Autoscaler burst load tests | **Yes** |
| **7.3** | ACT-15 | In-Guest Wake Hygiene & PRNG Reset (Story 6.3) | 6 turns / 1.0h | 10 turns / 2.0h | 16 turns / 3.5h | **10.3 turns / 2.1h** | Medium | In-guest clock/PRNG verification script | No |
| **7.4** | ACT-18 | Idle Fleet Scale-Down & Reaper (Story 6.4) | 6 turns / 1.0h | 10 turns / 2.0h | 16 turns / 3.5h | **10.3 turns / 2.1h** | High | Reaper idle timeout test suite | **Yes** |
| **8.0** | ACT-19 | Phase 1 Integrated Acceptance Gate | 10 turns / 2.0h | 15 turns / 4.0h | 24 turns / 7.0h | **15.7 turns / 4.2h** | High | Full 12-benefit automated validation | **Yes** |

---

## 2. Roll-up method and critical path duration

### Critical Path Duration Calculation

$$\begin{aligned}
T_{\text{crit}} &= T_e(\text{ACT-01}) + T_e(\text{ACT-02}) + T_e(\text{ACT-04}) + T_e(\text{ACT-05}) + T_e(\text{ACT-07}) + T_e(\text{ACT-09}) \\
&\quad + T_e(\text{ACT-12}) + T_e(\text{ACT-16}) + T_e(\text{ACT-17}) + T_e(\text{ACT-18}) + T_e(\text{ACT-19}) \\
&= 1.1 + 2.6 + 4.2 + 3.1 + 2.1 + 2.7 + 3.7 + 2.6 + 2.6 + 2.1 + 4.2 \\
&= \mathbf{31.0\text{ clock hours}} \quad (\approx \mathbf{132\text{ agent turns}})
\end{aligned}$$

### Critical Path Variance and Confidence

$$\sigma_{\text{crit}}^2 = \sum_{i \in \text{Critical Path}} \sigma_i^2 \approx 0.06 + 0.17 + 0.69 + 0.34 + 0.17 + 0.25 + 0.44 + 0.17 + 0.17 + 0.17 + 0.69 = \mathbf{3.32\text{ hours}^2}$$

$$\sigma_{\text{crit}} = \sqrt{3.32} \approx \mathbf{1.82\text{ hours}}$$

Applying standard normal distribution:
- **84% Confidence ($+1\sigma$)**: $31.0 + 1.8 = \mathbf{32.8\text{ hours}}$
- **95% Confidence ($+2\sigma$)**: $31.0 + 3.6 = \mathbf{34.6\text{ hours}}$
- **99% Confidence ($+3\sigma$)**: $31.0 + 5.5 = \mathbf{36.5\text{ hours}}$

### Progress measurement and actuals tracking

As asynchronous agents execute stories:
1. Actual turns and clock duration are logged in `docs/registers/Story-Execution-Register.md`.
2. Any delta between $T_e$ and actuals automatically triggers a variance check. A variance exceeding $+20\%$ draws on the schedule reserve registered in [Schedule-Reserve-Register.md](Schedule-Reserve-Register.md).
