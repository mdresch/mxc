---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-08"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
process: "Formulate architectural decisions for predictive wake interception and activity-based time-series forecasting"
outputs:
  - "docs/07-architecture/ADR-010-predictive-wake-interception.md"
status: "Approved"
---

# ADR 010: Predictive Wake Interception & Activity-Based Time-Series Forecasting

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-08` Predictive Wake & Forecasting. Also touches `TP-02` (Ingress) and `TP-06` (Pool Hygiene).  
> **Inputs:** [Spark-Capture-Phase-2.md](../project-docs/Spark-Capture-Phase-2.md), [Ideation-Document-Phase-2.md](../project-docs/Ideation-Document-Phase-2.md), [Benefits-Statement-Phase-2.md](../project-docs/Benefits-Statement-Phase-2.md)  
> **Outputs:** ADR-010-predictive-wake-interception.md

---

## 1. Executive Summary

Phase 1 relied on reactive wake-up: the ingress proxy held incoming HTTP requests while waking dormant micro-instances in ~215–280 ms. While compliant with Phase 1 bounds ($< 800\text{ ms}$ TTFB), interactive enterprise users perceive sub-300ms delays.

`ADR-010` shifts the paradigm from **reactive wake** to **predictive wake**, delivering **0 ms perceived wake latency** through a two-tiered predictive engine:
1. **Micro-Prediction (Early TLS Interception):** Intercepting the TLS `ClientHello` packet and extracting Server Name Indication (SNI) to trigger VM resume concurrently during the TLS and TCP handshakes ($\ge 60\text{ ms}$ before HTTP payload completion).
2. **Macro-Prediction (Activity-Based Time-Series Forecasting):** Modeling tenant work patterns (shift start times, recurring payroll batches, geographic schedules) to pre-warm instances 60 seconds before traffic bursts.

---

## 2. Decision & Architectural Mechanics

1. **Early TLS SNI Interceptor:**
   - Ingress proxy operates in non-blocking sniffing mode on port 443.
   - Upon receiving the first TCP `SYN` + TLS `ClientHello`, the SNI hostname is parsed without waiting for the full TLS session establishment or HTTP request line.
   - If the tenant instance is `WarmPaused`, `Resume-VM` is fired immediately in background.
   - Handshake negotiation ($40\text{--}80\text{ ms}$) overlaps with VM resume, masking $\ge 50\%$ of physical wake latency.
2. **Activity-Based Workload Forecaster:**
   - Time-series sliding window model records tenant wake timestamps, day-of-week frequency, and user identity patterns.
   - Scheduled pre-warming triggers `POST /pool/warm` 60–120 seconds in advance of recurring peaks (e.g. 08:54 AM for a 08:55 AM shift).
   - Perceived wake latency drops to **0 ms** ($< 10\text{ ms}$ TTFB).
3. **Safety Fallback:**
   - In the event of an unpredicted cache miss, the JIT ingress reverse proxy holding buffer (`ADR-002`) provides a safe, lossless fallback with zero client errors.

---

## 3. Consequences & Trade-Offs

- **Positive:** Delivers perceived zero-latency responsiveness indistinguishable from an always-on dedicated server.
- **Negative:** False positive predictions may pre-warm an instance that is not leased, consuming transient host RAM.
- **Mitigation:** Unused pre-warmed instances are bounded by the 180s cooldown timer (`AC-05.4`) and returned to cold inventory.
