---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-04"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-004-paused-ram-standby.md"
---

# ADR 004: Paused RAM standby, trimmed before suspend

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Topic pillar:** `TP-04` Paused footprint. The 300 ms caller ceiling also touches `TP-02`. The warm checkpoint also touches `TP-03`.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-004-paused-ram-standby.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

An idle Windows Server that stays running keeps spending processor time. A stopped guest makes the next caller wait through a cold boot. The decision is a Hyper-V guest left `Paused` in host RAM, trimmed before suspend, so CPU and GPU sit at 0.0%, the image disks stay allocated, and `Resume-VM` finishes within 300 ms. The architecture suite already states the pause in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-004-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-004-2026-10-30.adjudication.json).

## 3. Context

1. Spark bad choice 1 and business-case Alternative 1 leave the server running. The next request is fast, and the idle machine keeps its processor cost. That alternative is rejected when the paused footprint holds. Sources: [Spark-Capture.md](../project-docs/Spark-Capture.md), [Business-Case.md](../project-docs/Business-Case.md).
2. `HYP-mxc-001` and `AC-03.1` require 0.0% host CPU for each `Paused` standby guest. Zero CPU does not free the image disks. The implementation plan says 10 standby VMs were verified at 0.0% CPU. That claim was not re-measured for the ideation document. The hypothesis stays `Formulated`. Source: [Ideation-Document.md](../project-docs/Ideation-Document.md).
3. `HYP-mxc-002` and `AC-03.3` require `Resume-VM` in at most 300 ms. The figure is a ceiling. A resume of 301 ms fails even when a later first byte still meets `HYP-mxc-003`. Lessons learned record 180–290 ms. No new live resume was timed for the ideation document. The hypothesis stays `Formulated`.
4. `HYP-mxc-005` says the fast wake is `Resume-VM` from `Paused` RAM at `baseline-hot-ready`, not a start from `Stopped`. The checkpoint is the production image's warm state (`TP-03`, `ADR-003`). A stopped guest misses the 800 ms first-byte ceiling. The 800 ms check itself stays with `ADR-002` (`TP-02`).
5. `HYP-mxc-007` and `BEN-01` keep paused RAM resident, CPU and GPU at 0.0%, and the parent VHDX plus any `.avhdx` allocated. `Suspend-VM` is the pause. `Save-VM` and a stopped guest are different states. A production guest has no GPU partition. No GPU counter has been read. The first reading is the test.
6. `HYP-mxc-012`, `BEN-10`, and `AC-03.2` trim the working set before `Suspend-VM`, to about 1.0–1.2 GB. On idle release the guest is restored to `baseline-hot-ready` and then suspended, so the paused size is the checkpoint size when that restore succeeds. Lessons learned also cite a trim under 700 MB. Those two figures are not the same measurement. `BEN-10` cannot pass until one figure is the target.
7. Catalog sizes are inventory, not a measured paused-guest total. `winserv2025-golden.vhdx` is 10.88 GB with a 64 GB cap. `winserv2025-mxc-dev.vhdx` is 39.25 GB with a 64 GB cap. Production images are planned, each with a 64 GB cap and no current size. The operator guide asks for at least 50 GB free on the NVMe tier. Source: [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md).
8. `HYP-mxc-018` is the future horizon already on the suite record: hot guests stay in RAM and deep guests stay on NVMe. The running pool uses paused RAM only. The hypothesis stays `Formulated`.

## 4. Decision

1. An idle guest is Hyper-V `Paused`, entered by `Suspend-VM` after the working set is trimmed. A guest left `Running` is the rejected idle default. A guest that is `Saved` or `Stopped` does not meet this decision.
2. Host CPU charged to each paused standby guest is 0.0%.
3. Host GPU charged to that same guest is 0.0%. A missing GPU partition counts as 0.0%, and the record says the partition was absent. The first GPU reading is the test.
4. Guest memory stays resident. A reading of 0 MB fails this decision. Trim runs while the vCPUs are still running, on the bake path and on pool replenishment. The target paused size is about 1.0–1.2 GB. The under-700 MB lessons figure is recorded beside it and is not this target until one number is chosen.
5. `Resume-VM` finishes in at most 300 ms because those pages stay in host RAM. A resume that waits on disk page-in fails. The 300 ms ceiling is the platform wake inside the caller path owned by `ADR-002`. The 800 ms first byte stays on that record.
6. The resumed guest is the one captured at `baseline-hot-ready`. The contents of that checkpoint stay with `ADR-003`.
7. For each paused guest the parent VHDX and any `.avhdx` that belongs to it stay on the host. Removing those files fails the decision. One, two, or three full copies are an example of that standing cost. A shared parent plus a per-guest `.avhdx` stores the parent once. The catalog gives no `.avhdx` size, so the example does not add one. This decision does not set a host capacity or a currency cost.

### 4.1 Review triggers

Revisit when the first GPU reading is taken, when one RAM figure is chosen for `BEN-10`, and before any claim that `HYP-mxc-018` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Leave Windows Server running | The idle machine keeps its processor cost. Spark bad choice 1 and business-case Alternative 1. Rejected when 0.0% CPU, 0.0% GPU, resident RAM, and allocated disks hold. |
| Turn the server off | The next caller waits through a 14–45 second boot. That alternative is the ingress decision, `ADR-002`. |
| `Save-VM` or a stopped guest as the warm state | Host RAM falls to 0 MB, and resume pays disk page-in. That misses the 300 ms ceiling. |
| Trim with a balloon driver after the pause | The vCPUs are frozen, so the balloon cannot run. Trim happens before `Suspend-VM`. |

## 6. Consequences

### Positive

An idle guest uses no processor and no graphics. Its trimmed RAM stays resident, so `Resume-VM` stays within 300 ms. The image disks remain allocated for the next wake.

### Negative

Host RAM must hold every paused guest at the trimmed size. Two RAM figures are still in the suite, so `BEN-10` cannot pass yet. GPU has no sample. No paused-guest disk total has been measured. `HYP-mxc-001`, `HYP-mxc-002`, `HYP-mxc-005`, `HYP-mxc-007`, and `HYP-mxc-012` stay `Formulated`.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 1 | Leave the server running and pay for an idle machine. | TP-04 | — |
| Spark | Disk stays allocated | Zero CPU does not free the image disks. | TP-04 | — |
| Spark | 300 ms unpause | Unpause to available is at most 300 ms. | TP-04 | — |
| Hypothesis | HYP-mxc-001 | A paused guest uses 0.0% host CPU. | TP-04 | — |
| Hypothesis | HYP-mxc-002 | Resume-VM finishes in at most 300 ms. | TP-04 | — |
| Hypothesis | HYP-mxc-005 | The fast wake is resume from the hot checkpoint, not a cold boot. | TP-04 | TP-03 |
| Hypothesis | HYP-mxc-007 | Paused RAM stays resident. CPU and GPU stay at 0.0%. Disk stays allocated. | TP-04 | — |
| Hypothesis | HYP-mxc-012 | Trim before pause, to about 1.0–1.2 GB. | TP-04 | — |
| Hypothesis | HYP-mxc-018 | Future: hot guests in RAM, deep guests on NVMe. | TP-04 | ADR-004 horizon |
| Benefit | BEN-01 | Idle processor and graphics, with RAM and image disks still allocated. | TP-04 | — |
| Benefit | BEN-10 | Paused size is the trimmed checkpoint, about 1.0–1.2 GB. | TP-04 | — |
| Business case | Alternative 1 | Leave Windows Server running. Rejected if the paused footprint holds. | TP-04 | — |

`HYP-mxc-018` is the future horizon already noted on the architecture-suite ADR: a hot set in paused RAM and a deep set saved to NVMe. No saved-to-NVMe tier has been measured.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-004`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Wake story: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `US-03` (`AC-03.1` through `AC-03.3`)
- Caller-visible 800 ms, not decided here: architecture-suite `ADR-002`
- Warm checkpoint, not decided here: architecture-suite `ADR-003`
