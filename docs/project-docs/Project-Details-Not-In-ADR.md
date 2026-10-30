---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation"
lifecycle_stage: "Stage 1 (Intent) and Stage 4 (Benefit)"
governance_policy: "none — draft only, not an approval gate"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Draft project details that the topic pillars cover and ADR-001 through ADR-006 do not mention"
outputs:
  - "Project-Details-Not-In-ADR.md"
---

# Project details not yet in an ADR

> **Sources:** [Spark-Capture.md](Spark-Capture.md), [Ideation-Document.md](Ideation-Document.md), [Business-Case.md](Business-Case.md), [Benefits-Statement.md](Benefits-Statement.md)  
> **Compared with:** [ADR.md](../hyperv/architecture/ADR.md) (`ADR-001` through `ADR-006`)  
> **Date:** 2026-10-30  
> **Status:** Draft. These are not decisions. Each item names the topic pillar and the ADR that would have to mention it.

Topic pillars `TP-01` through `TP-06` already assign one primary ADR each. This note lists claims from the spark, the hypotheses, and the benefits register that those six records do not mention.

Currency, density, and license savings stay out. The business case and the benefits statement already refuse them.

---

## TP-01 Isolation — recorded in ADR-001

`ADR-001` now carries the `TP-01` rows: the shared-kernel rejection, the Generation 2 subsystems, and the paused-versus-running risk comparison. `PD-01` is no longer an open gap. The RAM, CPU, GPU, and disk readings stay with `ADR-004`.

---

## TP-02 Ingress — recorded in ADR-002

`ADR-002` now carries the `TP-02` rows: the held request, both routing rules, the 800 ms first byte, the rejection of a cold boot, and sign-in on that wake. `PD-02`, `PD-03`, and `PD-04` are no longer open gaps. The 300 ms `Resume-VM` reading stays with `ADR-004`. Kerberos `:88` stays with `ADR-005`. The clock step stays with `ADR-006`. The second-factor product is still unnamed.

---

## TP-03 Image supply — recorded in ADR-003

`ADR-003` carries the `TP-03` rows: a production image with no developer toolchain, checkpointed at `baseline-hot-ready`, and a future rule that a pool accepts only a signed, scanned image. `HYP-mxc-017` stays `Formulated` on that horizon. `BEN-08` stays unrealized while `winserv2025-prod-adpa.vhdx` is still absent from the catalog. Session discard stays with `ADR-005`. Paused RAM stays with `ADR-004`.

---

## TP-04 Paused footprint — recorded in ADR-004

`ADR-004` now carries the `TP-04` rows: 0.0% CPU, 0.0% GPU, resident RAM trimmed to about 1.0–1.2 GB before suspend, `Resume-VM` within 300 ms, and image disks that stay allocated. `PD-05` and `PD-06` are no longer open gaps. The 800 ms first byte stays with `ADR-002`. The warm checkpoint stays with `ADR-003`. The under-700 MB trim note is a different figure, so `BEN-10` still needs one chosen target. GPU has no sample yet. `HYP-mxc-018` stays `Formulated` on the NVMe horizon.

---

## TP-05 Session sterility — recorded in ADR-005

`ADR-005` now carries the `TP-05` rows: session writes only on a transient `.avhdx`, the egress whitelist, and both discards. The whole guest can be removed, or only the `.avhdx`. Either way the next session is reproduced from the approved production image. `PD-07` is no longer an open gap. `BEN-12` stays open while `BEN-08` waits on the production bake. `HYP-mxc-019` stays `Formulated` on the memory-scratch horizon. Entropy reseed, the clock step, and the database-pool purge stay with `ADR-006`.

---

## TP-06 Pool and wake hygiene — recorded in ADR-006

`ADR-006` now carries the `TP-06` rows: refill in about 1.5 seconds, wake hygiene before traffic, and a future forecast pre-warm. `PD-08` is no longer an open gap. The surge check records whether the configured figure was above 5 requests per second or 10 or more over 5 seconds. `BEN-09` still cannot pass until one surge figure is chosen. The cooldown check likewise records 300 seconds or 180 seconds. `HYP-mxc-020` stays `Formulated` on the forecast horizon. Paused RAM stays with `ADR-004`. Session discard stays with `ADR-005`.

---

## What this draft does not reopen

These are already mentioned in an ADR, so they are not drafted again:

| Detail | Where it already sits |
|---|---|
| Hyper-V Generation 2 instead of a shared kernel, including WMI, COM+, services, and Group Policy, and a paused guest as the smaller attack window | `ADR-001` |
| Held request, both routes, 800 ms first byte, no wake-caused 502 or 504, and sign-in on that wake | `ADR-002` |
| Production image without Scoop, cargo, git, or compilers, checkpointed at `baseline-hot-ready`. A signed, scanned image stays the future horizon | `ADR-003` |
| `Paused` at 0.0% CPU and 0.0% GPU, RAM trimmed to about 1.0–1.2 GB before suspend, `Resume-VM` within 300 ms, image disks still allocated | `ADR-004` |
| Session writes only on a transient `.avhdx`, both discards, reproduce from the approved production image, egress whitelist including Kerberos `:88` | `ADR-005` |
| Refill in about 1.5 seconds, both surge figures named on the check, entropy reseed, clock step, database-pool purge, cooldown at the configured 300 s or 180 s. A forecast pre-warm stays the future horizon | `ADR-006` |
| Future micro-VM, long-lived streams, signed images, NVMe deep tier, memory scratch, and forecast pre-warm | The future-horizon note on the matching ADR |
