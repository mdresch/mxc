---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-006-watermark-pool.md"
  - "docs/project-docs/Business-Requirements/BRD-006-watermark-pool.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-006-watermark-pool.md"
---

# FDD-006: Watermark pool, replenish, and wake hygiene

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-006](../../07-architecture/ADR-006-watermark-pool.md), [BRD-006](../Business-Requirements/BRD-006-watermark-pool.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-006-watermark-pool.md

**Source ADR:** [ADR-006](../../07-architecture/ADR-006-watermark-pool.md) — Accepted.  
**Source BRD:** [BRD-006](../Business-Requirements/BRD-006-watermark-pool.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-006-2026-10-30.adjudication.json](../gates/approve-fdd-006-2026-10-30.adjudication.json).

## Design

### Pool controller (`FDD.md` §2.2)
* States: `ColdProvisioned` → `StandbyPaused` → `ActiveRunning`.
* `pool_config.json`: `min_ready_standby`, `max_ready_standby`, `surge_velocity_threshold_rps` (example 10), queue depth trigger.
* Async worker promotes next guest after lease (`AC-05.1`).
* Pre-warm: `mxc-pool-warm --target prod-adpa --count N` / `POST /pool/warm` (`AC-05.3`).

### Wake hygiene on `/health` (`FDD.md` §2.3, `AC-02.4`)
1. PRNG reseed from hardware.
2. Guest clock within 50 ms of host UTC.
3. Database connection pools cleared.

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Ready pool empty under surge | Expand toward K_max; do not cold-provision caller without recording threshold |
| /health before hygiene complete | Do not accept traffic; sign-in and TLS depend on clock step (`ADR-002`) |

## Out of Scope

- Paused RAM size per guest (`ADR-004`).
- `.avhdx` discard rules (`ADR-005`).
- Forecast model (`HYP-mxc-020` horizon).
