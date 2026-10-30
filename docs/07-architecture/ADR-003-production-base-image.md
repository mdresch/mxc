---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-03"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-003-production-base-image.md"
---

# ADR 003: Production base image separate from the developer image

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Topic pillar:** `TP-03` Image supply. This decision has no second pillar.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-003-production-base-image.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

Production and development currently share the image catalog's developer disk. The decision is a separate production base image, `winserv2025-prod-adpa.vhdx`, with no developer toolchain and a warm checkpoint named `baseline-hot-ready`. That file is not in the catalog yet, so the benefit stays unrealized. The architecture suite already states this choice in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-003-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-003-2026-10-30.adjudication.json).

## 3. Context

1. `HYP-mxc-011` states that production runs from `winserv2025-prod-adpa.vhdx`, not from the developer golden image. Compilers, Scoop, cargo, git, and developer SDKs are absent. `baseline-hot-ready` is taken after a smoke request, so the first wake does not pay a JIT compile. The hypothesis stays `Formulated`. Source: [Ideation-Document.md](../project-docs/Ideation-Document.md).
2. `BEN-08` is an inventory of that production VHDX: no Scoop, cargo, git, or compiler, and a checkpoint taken after a warm-up request. The benefit stays unrealized while the production bake is still active. Source: [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
3. The image catalog lists `winserv2025-mxc-dev.vhdx` (`img-mxc-dev-v2.3`) as `baked_ready` with the developer toolchain, and `winserv2025-golden.vhdx` (`img-os-ws2025-base`) as the OS parent used to stamp new images. `winserv2025-prod-adpa.vhdx` is absent. `img-adpa-poc-v1` is `poc_planned`. Source: [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md).
4. User story `US-04` already names the checks. `AC-04.1` requires the production VHDX to contain the compiled application, Windows runtime dependencies, and a hardened profile, with compilers, Scoop, uv, cargo, and source repositories absent. `AC-04.2` starts the service, probes `localhost:8080/health`, closes database handles, and captures `baseline-hot-ready` while the working set is hot. Source: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md).
5. `HYP-mxc-017` is the future horizon already on the suite record: a pool accepts only a signed, scanned image. The bake path does not sign images or emit a bill of materials today. The hypothesis stays `Formulated`.
6. Session discard and the egress whitelist stay with `ADR-005`. The paused RAM reading stays with `ADR-004`. The wake-time database-pool purge stays with `ADR-006`.

## 4. Decision

1. The production pool runs from `winserv2025-prod-adpa.vhdx`. That image is separate from the developer image `winserv2025-mxc-dev.vhdx`.
2. `winserv2025-golden.vhdx` may stamp a new workload image. It is not the parent the production pool runs.
3. A file inventory of the production VHDX finds no Scoop, cargo, git, or compiler. `AC-04.1` also requires uv and source repositories to be absent.
4. The bake captures checkpoint `baseline-hot-ready` after the service has answered a smoke request on `localhost:8080/health` and database handles are closed. A wake from that checkpoint serves the first request without a JIT compilation stall.
5. Windows Server 2025 Server Core, or a CIS-hardened Desktop Experience, is the operating system. Print Spooler, Xbox, and telemetry services are disabled. ADPA / SIDPA is a pre-jitted Windows service under a local service account with least privilege.
6. This decision does not discard a session disk, set paused RAM, or sign the image. Signing and vulnerability scanning stay on the `HYP-mxc-017` horizon until a bake emits a signature and a bill of materials.

### 4.1 Review triggers

Revisit when `winserv2025-prod-adpa.vhdx` is in the catalog and an inventory for `BEN-08` can be run, and before any claim that `HYP-mxc-017` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Run production from `winserv2025-mxc-dev.vhdx` | That disk carries the developer toolchain. `HYP-mxc-011` and `BEN-08` require a separate production image. |
| Run the production pool from `winserv2025-golden.vhdx` | That disk is the OS stamp parent. The hypothesis requires it not to be the production pool parent. |
| Treat the ADPA proof-of-concept image as the production image | `img-adpa-poc-v1` is `poc_planned` and uses `winserv2025-adpa-poc.vhdx`. It is not `winserv2025-prod-adpa.vhdx`. |

## 6. Consequences

### Positive

A finished production image is not a developer image. It has no developer toolchain, and its warm checkpoint is `baseline-hot-ready`.

### Negative

`winserv2025-prod-adpa.vhdx` is not in the catalog, so `BEN-08` cannot be claimed as realized. `HYP-mxc-011` stays `Formulated`. The suite names both `winserv2025-golden.vhdx` and `winserv2025-mxc-dev.vhdx` in the developer lineage. The inventory has to record which file was the parent. An unsigned image can still be registered until the future horizon is built.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Hypothesis | HYP-mxc-011 | The production image has no developer toolchain and is checkpointed warm. | TP-03 | — |
| Hypothesis | HYP-mxc-017 | Future: a pool accepts only a signed, scanned image. | TP-03 | ADR-003 horizon |
| Benefit | BEN-08 | The production image is not a developer image. | TP-03 | — |

`HYP-mxc-017` is the future horizon already noted on the architecture-suite ADR: vulnerability scan, software bill of materials, and a signature check before pool registration. No such bake has been run.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-003`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Image catalog: [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md)
- Bake checks: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `US-04`
- Session discard, not decided here: architecture-suite `ADR-005`
- Paused RAM, not decided here: architecture-suite `ADR-004`
