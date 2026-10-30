---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-05"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-005-transient-differencing-disk.md"
---

# ADR 005: Transient differencing disk and egress whitelist

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Topic pillar:** `TP-05` Session sterility. The approved production image also touches `TP-03`.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-005-transient-differencing-disk.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

A session that writes onto a lasting disk leaves residue for the next caller. The decision is that every production session writes only to a transient `.avhdx`, that either the whole guest or only that disk is discarded, and that the next session is reproduced from the approved production image. Public internet egress is denied. The named internal ports stay allowed. The architecture suite already states the differencing disk and the whitelist in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-005-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-005-2026-10-30.adjudication.json).

## 3. Context

1. The spark discards either the whole Hyper-V guest or only its `.avhdx`, then reproduces the next session from the approved production image. Source: [Spark-Capture.md](../project-docs/Spark-Capture.md).
2. `HYP-mxc-013` and `BEN-07` require session writes on a transient `.avhdx` anchored at `baseline-hot-ready`. After the session ends, or after 300 seconds with no open requests, that disk is discarded and the guest returns to the baseline. A file written in the guest is gone. The parent baseline hash is unchanged. Public internet egress is dropped. SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88` to approved internal endpoints are allowed. Port-ACL automation is recorded as implemented in the lessons note. Milestone 3.2 still marks the ACL work active. No new packet capture was taken. The hypothesis stays `Formulated`. Sources: [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
3. `HYP-mxc-022` and `BEN-12` require both discards. The whole guest can be removed, or only the `.avhdx`. In both cases the next parent matches the approved production image and does not match the developer image. No discard-and-reproduce run has been captured. `BEN-12` stays open while `BEN-08` waits on a finished production bake. The hypothesis stays `Formulated`.
4. The approved image is `winserv2025-prod-adpa.vhdx`. What counts as the developer image, and the fact that this production file is not in the catalog yet, stay with `ADR-003` (`TP-03`).
5. User story `US-02` already names the checks. `AC-02.1` deletes the `.avhdx` on release or after 300 seconds with no open requests, and ends a hung request at 900 seconds with HTTP 504. `AC-02.2` requires the SHA-256 of `winserv2025-prod-adpa.vhdx` to stay identical. `AC-02.3` is the whitelist. `AC-02.4` reseeds entropy, steps the clock, and clears database pools. Those three wake steps stay with `ADR-006`. Source: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md).
6. `HYP-mxc-019` is the future horizon already on the suite record: session scratch lives in memory and is wiped on release. Sessions still use a file-backed `.avhdx`. The hypothesis stays `Formulated`.

## 4. Decision

1. Every production session writes only to a transient `.avhdx` anchored at `baseline-hot-ready`. Persistent business data lives in external datastores.
2. **Differencing disk only.** The guest remains. On session end, or after 300 seconds with `active_open_requests` at 0, the `.avhdx` is deleted. A file written only on that disk is gone. The parent hash is unchanged. The guest returns to `baseline-hot-ready` before it re-enters the warm pool.
3. **Whole guest.** The Hyper-V session is removed. A file written only in that guest is gone. The next guest is a new reproduction from the approved production image. This path stays open while that image is unfinished.
4. In both paths the next session's parent matches the approved production image and does not match the developer image. The next session does not inherit disk changes from the previous one.
5. Public internet egress is denied. Ingress reaches the guest only on `:8080` from the proxy. Allowed egress, to approved internal endpoints, is SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88`. Every other outbound destination is dropped and logged.
6. A request that hangs past 900 seconds ends with HTTP 504, then the instance is reaped. That 504 is a hung request. Wake-caused 502 and 504 stay with `ADR-002`.
7. This decision does not set the production image contents, the paused footprint, or the wake-time entropy, clock, and database-pool steps.

### 4.1 Review triggers

Revisit when `winserv2025-prod-adpa.vhdx` exists so both discard paths in `BEN-12` can be run, and before any claim that `HYP-mxc-019` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Keep session writes on the parent disk | The next session inherits files, logs, and registry changes. `BEN-07` requires that residue to be gone. |
| Discard only the `.avhdx` | That path stays valid. The spark and `HYP-mxc-022` also allow removing the whole guest. One path does not retire the other. |
| Reproduce the next session from the developer image | The parent must be the approved production image. Which file that is stays with `ADR-003`. |
| Allow public internet egress | `AC-02.3` denies it. Persistent data uses the named internal ports. |

## 6. Consequences

### Positive

Session residue does not remain on either discard path. The next session is reproduced from the approved production image. Egress stays on the named whitelist.

### Negative

Both paths have to be checked. `BEN-12` cannot pass until the production image exists. A file-backed `.avhdx` is still the scratch disk. `HYP-mxc-013` and `HYP-mxc-022` stay `Formulated`. The lessons note and Milestone 3.2 disagree on whether the port ACL is finished, so `BEN-07` still needs a packet capture.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Discard and reproduce | Discard the whole guest or only the .avhdx, then reproduce from the approved image. | TP-05 | TP-03 |
| Hypothesis | HYP-mxc-013 | Session disk writes disappear. Egress stays on the whitelist. | TP-05 | — |
| Hypothesis | HYP-mxc-022 | Discard the whole guest or only the .avhdx, then reproduce from the approved image. | TP-05 | TP-03 |
| Hypothesis | HYP-mxc-019 | Future: session scratch in memory, wiped on release. | TP-05 | ADR-005 horizon |
| Benefit | BEN-07 | Session residue does not remain. | TP-05 | — |
| Benefit | BEN-12 | Discard and reproduce from the approved production image. | TP-05 | TP-03 |

`HYP-mxc-019` is the future horizon already noted on the architecture-suite ADR: a write-once memory disk over VMBus, wiped on release. No such disk has been measured.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-005`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Session story: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `US-02`
- Approved production image, not decided here: architecture-suite `ADR-003`
- Wake hygiene, not decided here: architecture-suite `ADR-006`
