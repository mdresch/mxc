---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-01"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-001-type-1-hyperv-generation-2.md"
---

# ADR 001: Type-1 Hyper-V Generation 2 instead of a container namespace

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic pillar:** `TP-01` Isolation. The paused footprint readings stay with `TP-04`.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-001-type-1-hyperv-generation-2.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

ADPA and SIDPA process confidential records and sit idle between requests. A shared-kernel container does not meet that isolation bar. The decision is a Type-1 Hyper-V Generation 2 guest, paused while idle, so the workload keeps its own kernel and the Windows subsystems a container drops. The architecture suite already states this choice in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy in the designated ADR folder.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-001-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-001-2026-10-30.adjudication.json).

## 3. Context

1. The spark's third bad choice is a container that shares the host kernel. The records are financial, personal, or otherwise something a neighbor workload must not reach. Source: [Spark-Capture.md](../project-docs/Spark-Capture.md).
2. `HYP-mxc-006` states the same bar and stays `Formulated`. Source: [Ideation-Document.md](../project-docs/Ideation-Document.md).
3. Business-case Alternative 3 rejects the shared-kernel container for those records. Source: [Business-Case.md](../project-docs/Business-Case.md).
4. `HYP-mxc-009` and `BEN-05` require WMI, COM+, native Windows services, and Group Policy on a Generation 2 guest. The same calls fail or are unsupported in a container namespace. Sources: [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
5. The spark, `HYP-mxc-021`, and `BEN-11` say a paused guest is a smaller security risk than the same guest left running. While `Paused`, a direct connection to the guest service port fails. A new session starts only after the gateway resumes the guest. Time spent paused is time the guest is not executing workload code.
6. [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-002` says the paused socket is unreachable so the gateway can hold the request. That is a delivery fact. The security comparison belongs here.
7. [docs/hyperv/architecture/FDD.md](../hyperv/architecture/FDD.md) and [docs/hyperv/architecture/USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) do not state Generation 2, WMI, COM+, Group Policy, or the container rejection. The lifecycle BRD folder still holds only `BRD-TEMPLATE.md`.

## 4. Decision

1. The workload runs in a Type-1 Hyper-V Generation 2 virtual machine. The control plane is `wxc-exec --features hyperv`. The guest kernel is not the host kernel.
2. A shared-kernel container does not meet the isolation bar for ADPA and SIDPA.
3. WMI, COM+, a Windows service, and Group Policy are required to succeed in that guest.
4. An idle guest is `Paused`, not left `Running`. A direct connection to the guest service port fails while it is paused. A new session starts only after the gateway resumes the guest.
5. This decision does not set the 0.0% CPU reading, the resident RAM, the GPU reading, or the allocated image disks. Those stay with `ADR-004` in the architecture suite (`TP-04`).

### 4.1 Review triggers

Revisit before the first side-by-side subsystem check named in `BEN-05`, and before any claim that `HYP-mxc-015` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Leave a Windows Server running so the next request is fast | The idle machine keeps executing and keeps accepting connections. That is the higher-risk case in `HYP-mxc-021` and `BEN-11`. |
| Turn the server off | The next caller waits through a cold boot. That alternative is the wake decision, not this one. |
| Shared-kernel container | Rejected for confidential records. Spark bad choice 3, `HYP-mxc-006`, and business-case Alternative 3. The named Windows subsystems do not survive the namespace (`HYP-mxc-009`, `BEN-05`). |

## 6. Consequences

### Positive

The workload has its own kernel. The named Windows subsystems stay in scope. An idle guest is paused, so it is not executing and not accepting a new session.

### Negative

The host must be Windows Pro, Enterprise, or Windows Server with Hyper-V enabled. A paused guest still occupies host RAM and its image disks. Those costs are outside this decision. Lifecycle `BRD-001`, `FDD-001`, and `epic-001` draft the tests; they are not yet approved under `approve-brd`, `approve-fdd`, or `approve-user-stories`. `HYP-mxc-006`, `HYP-mxc-009`, and `HYP-mxc-021` stay `Formulated`.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 3 | A shared-kernel container is not enough for confidential records. | TP-01 | — |
| Spark | Closed idle guest | A paused machine is a smaller security risk than one left running. | TP-01 | TP-04 |
| Hypothesis | HYP-mxc-006 | A shared kernel does not meet the isolation bar. | TP-01 | — |
| Hypothesis | HYP-mxc-009 | A Generation 2 guest keeps WMI, COM+, services, and Group Policy. | TP-01 | — |
| Hypothesis | HYP-mxc-021 | A closed idle guest is a smaller security risk than a running one. | TP-01 | TP-04 |
| Hypothesis | HYP-mxc-015 | Future: paused micro-VM under 256 MB. | TP-01 | ADR-001 horizon |
| Benefit | BEN-05 | Windows work stays on its own guest. | TP-01 | — |
| Benefit | BEN-11 | A closed idle guest accepts no new session. | TP-01 | TP-04 |
| Business case | Alternative 3 | Use a shared-kernel container. Rejected for confidential records. | TP-01 | — |

`HYP-mxc-015` is the future horizon already noted on the architecture-suite ADR: a paused micro-VM under 256 MB. No such image has been measured.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-001`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Paused footprint, not decided here: architecture-suite `ADR-004`
