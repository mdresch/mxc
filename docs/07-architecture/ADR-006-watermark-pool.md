---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-06"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-006-watermark-pool.md"
---

# ADR 006: Watermark pool, replenish, and wake hygiene

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Topic pillar:** `TP-06` Pool and wake hygiene. Queue depth also touches `TP-02`. RAM per extra guest also touches `TP-04`. Discard on cooldown also touches `TP-05`.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-006-watermark-pool.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

One paused guest serves one caller. A burst that leases it leaves the next caller with a cold provision. The decision is a watermark pool that refills a ready guest in about 1.5 seconds, expands up to a configured cap when a named surge figure trips, and runs entropy, clock, and database-pool hygiene before traffic. The architecture suite already states the pool in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-006-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-006-2026-10-30.adjudication.json).

## 3. Context

1. `HYP-mxc-014` states that leasing the last ready guest promotes a `ColdProvisioned` guest to `StandbyPaused` in about 1.5 seconds, without blocking the in-flight request. A surge raises the ready count up to \(K_{\max}\). Before traffic, the guest reseeds randomness from hardware, steps the clock to host UTC, and clears stale database pools. Surplus guests leave `ActiveRunning` after 300 seconds with no open requests. No surge run was captured. The hypothesis stays `Formulated`. Source: [Ideation-Document.md](../project-docs/Ideation-Document.md).
2. `BEN-09` is that refill, that `/health` report, and that cooldown. It says 5 requests per second and 10 requests per second are not the same target, and the check must record which threshold was configured. Source: [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
3. The suite carries both figures. This record's former example is above 5 requests per second, or an ingress queue depth above 0. [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md) uses 10 or more requests per second over a rolling 5-second window, scaling from \(K_{\min} = 1\) to \(K_{\max} = 5\). [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `AC-05.2` uses above 10 requests per second, or queue depth above 0, up to 5 ready instances. [FDD.md](../hyperv/architecture/FDD.md) stores `surge_velocity_threshold_rps: 10`.
4. `AC-05.1` is the background refill. `AC-05.3` is an explicit pre-warm (`POST /pool/warm`). `AC-05.4` reaps surplus guests after `reaping_cooldown_seconds` of 180 seconds. `HYP-mxc-014` and `BEN-09` use 300 seconds. Those cooldowns are not the same figure.
5. `HYP-mxc-020` is the future horizon already on the suite record: a forecast pre-warms the pool about 60 seconds ahead, with no manual schedule. Pre-warm today is an explicit command or a surge reaction. No forecast model is running. The hypothesis stays `Formulated`.
6. The paused RAM reading stays with `ADR-004`. Discard of the differencing disk stays with `ADR-005`. The 800 ms first byte and the sign-in product stay with `ADR-002`. The clock step this decision requires is the piece sign-in waits on.

## 4. Decision

1. Pool states run `ColdProvisioned` → `StandbyPaused` → `ActiveRunning`. `ColdProvisioned` is a differencing disk on NVMe at 0 MB host RAM. It is inventory, not the paused standby.
2. When a ready guest is leased, a background worker promotes the next guest to `StandbyPaused` in about 1.5 seconds. The in-flight request is not blocked. The default ready count is at least 1.
3. A surge raises the ready count up to the configured \(K_{\max}\). The check records which surge figure was configured:
   - Above 5 requests per second, or ingress queue depth above 0.
   - 10 or more requests per second over a rolling 5-second window.
   A pass at one figure does not pass the other. Until one figure is chosen, `BEN-09` cannot treat them as a single target. Suite examples of \(K_{\max}\) are 5 and 5–10. The check records the configured cap.
4. `mxc-pool-warm --target prod-adpa --count N` can raise the ready count before a known peak. That command is not a forecast.
5. The first `/health` after wake reports three steps before the guest accepts traffic: entropy reseeded from hardware, the guest clock stepped to host UTC, and database connection pools cleared.
6. After the configured idle time with no open requests, surplus guests above \(K_{\min}\) leave `ActiveRunning`, their differencing disks are discarded, and the pool returns toward the low watermark. The check records whether that idle time was 300 seconds or 180 seconds.
7. This decision does not set the paused RAM size, the session-discard rules, or a forecast model.

### 4.1 Review triggers

Revisit when one surge figure is chosen for `BEN-09`, when one cooldown figure is chosen, and before any claim that `HYP-mxc-020` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Keep a single warm guest and cold-provision the next caller | The next caller waits through a boot. `BEN-09` requires a refill that does not cold-boot that caller. |
| Treat above 5 requests per second and 10 requests per second as one threshold | The lessons note, `AC-05.2`, and the functional-design example use the 10-request figure. The former suite example uses 5. A pass at one does not pass the other. |
| Treat 180 seconds and 300 seconds as one cooldown | `AC-05.4` uses 180 seconds. `HYP-mxc-014` and `BEN-09` use 300 seconds. |
| Run a forecast model as the current pre-warm | No forecast model is running. Pre-warm today is an explicit command or a surge reaction. `HYP-mxc-020` stays `Formulated`. |

## 6. Consequences

### Positive

A burst refills the ready pool in about 1.5 seconds. Wake hygiene runs before traffic. The next caller does not cold-boot when the configured surge expands the pool.

### Negative

Each extra paused guest holds the `ADR-004` RAM footprint until cooldown. `BEN-09` cannot pass while two surge figures remain. The cooldown check has the same split between 180 seconds and 300 seconds. `HYP-mxc-014` stays `Formulated`.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Hypothesis | HYP-mxc-014 | The warm pool refills, and wake hygiene runs before traffic. | TP-06 | — |
| Hypothesis | HYP-mxc-020 | Future: a forecast pre-warms the pool about 60 seconds ahead. | TP-06 | ADR-006 horizon |
| Benefit | BEN-09 | A burst does not cold-boot the next caller. | TP-06 | — |

`HYP-mxc-020` is the future horizon already noted on the architecture-suite ADR: an on-host forecast that pre-warms about 60 seconds ahead. No such model has been run.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-006`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Pool story: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `US-05`
- Paused RAM per extra guest, not decided here: architecture-suite `ADR-004`
- Discard on cooldown, not decided here: architecture-suite `ADR-005`
- Ingress queue, not decided here: architecture-suite `ADR-002`
