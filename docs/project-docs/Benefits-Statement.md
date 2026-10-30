---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Business Documents / Benefits Realization Planning"
lifecycle_stage: "Stage 4 (Benefit)"
governance_policy: "approve-business-case"
inputs:
  - "Business-Case.md"
  - "Hypothesis expected value premises"
process: "Quantify measurable target benefits, metric thresholds, and realization sequence"
outputs:
  - "Benefits-Statement.md (Mandatory input to Project Charter)"
---

# Benefits Statement — Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

> **PMBOK 8 Process:** `Business Documents / Benefits Realization Planning` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 4 (Benefit)`  
> **Inputs:** [Business-Case.md](Business-Case.md), [Ideation-Document.md](Ideation-Document.md) (`HYP-mxc-001` through `HYP-mxc-014`)  
> **Process:** Quantify measurable target benefits, metric thresholds, and realization sequence  
> **Outputs:** Benefits-Statement.md (Mandatory input to the project charter)

**Source:** [Business-Case.md](Business-Case.md)  
**Date:** 2026-10-29  
**Project Name:** MXC Hyper-V for ADPA / SIDPA  
**Project Description:** Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes  
**Accountable benefit owner:** Menno Drescher for the operational checks below. No finance owner is named, because no money benefit is claimed.  
**Status:** Draft. This statement is a charter input. The charter is not started.

`HYP-mxc-015` through `HYP-mxc-020` are research hypotheses. They do not appear in the register.

---

## Benefits register

| Benefit | Measure | Target | Owner | Check |
|---|---|---|---|---|
| `BEN-01` Idle processor and graphics | Host CPU and GPU charged to a `Paused` guest, plus disk still allocated to its images | 0.0% CPU and 0.0% GPU. RAM still assigned. Parent VHDX and any `.avhdx` still allocated. | Menno Drescher | `HYP-mxc-001`, `HYP-mxc-007`. Read the host counters on a paused standby guest. A 0 MB RAM reading fails the benefit. A missing image disk fails it too. GPU has no prior sample, so the first reading is the test, not a confirmation. |
| `BEN-02` Wake without a cold boot | Time from request arrival on a paused guest to `Resume-VM` complete, and to the first response byte | ≤ 300 ms to unpause. ≤ 800 ms to the first byte. | Menno Drescher | `HYP-mxc-002`, `HYP-mxc-003`. Time a cold wake. Warm traffic after the guest is already running does not count. |
| `BEN-03` No wake-caused gateway failure | HTTP status of a request that arrived while the guest was paused | Not 502 and not 504 because of the wake. | Menno Drescher | `HYP-mxc-010`. Use an ordinary HTTPS client. A 503 after the wake timeout is a different case and does not pass this benefit. |
| `BEN-04` Request lands on the owning image | Pool selected for `/api/v1/adpa` and `/api/v1/sidpa`, and image selected for listen ports `:8090`, `:8091`, and `:8092` | Path selects `prod-adpa` or `prod-sidpa`. Catalogued port selects the image bound to that port. Guest service port is `:8080`. | Menno Drescher | `HYP-mxc-004`. Record which rule fired. The two rules are not yet one benefit. |
| `BEN-05` Windows work stays on its own guest | WMI, COM+, a Windows service, and Group Policy inside the guest, compared with a container namespace | Those calls succeed on the Generation 2 guest and fail or are unsupported in the container. | Menno Drescher | `HYP-mxc-006`, `HYP-mxc-009`. One side-by-side pass. |
| `BEN-06` Sign-in does not wait on boot | A username, a password, and a second factor against a guest that was paused when the request arrived | No 25–45 second boot in the user-visible wait. Wake itself still meets `BEN-02`. Clock is stepped to the host before sign-in is accepted. | Menno Drescher | `HYP-mxc-008`. Time spent typing is outside the 300 ms and 800 ms ceilings. The second-factor product is still unnamed, so the check cannot be scripted until that name exists. |
| `BEN-07` Session residue does not remain | A file written during the session, the parent image hash, and a probe to a public address | The file is gone after release. The parent hash is unchanged. Public egress is dropped. SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88` to approved internal endpoints are allowed. | Menno Drescher | `HYP-mxc-013`. |
| `BEN-08` Production image is not a developer image | Inventory of `winserv2025-prod-adpa.vhdx` | No Scoop, cargo, git, or compiler. Checkpoint `baseline-hot-ready` was taken after a warm-up request. | Menno Drescher | `HYP-mxc-011`. This benefit stays unrealized while the production bake is still active. |
| `BEN-09` A burst does not cold-boot the next caller | Time to a new `StandbyPaused` guest after a lease, and `/health` after wake | About 1.5 seconds to refill. Health reports entropy reseeded, clock synced, and database pools cleared. Surplus guests leave `ActiveRunning` after 300 seconds with no open requests. | Menno Drescher | `HYP-mxc-014`. Do not treat 5 requests per second and 10 requests per second as the same target. Record which threshold was configured for the check. |
| `BEN-10` Paused size is the trimmed checkpoint | Host RAM of a `Paused` guest after release | About 1.0–1.2 GB, taken from the checkpoint that was trimmed before it was stamped. | Menno Drescher | `HYP-mxc-012`, `HYP-mxc-005`. The under-700 MB figure in the lessons note is not this target. One number has to be chosen before this benefit can pass or fail. |
| `BEN-11` Closed idle guest | Time the guest spends paused, and whether it accepts a connection in that state | While `Paused`, a direct connection to the guest service fails. A new session starts only after resume. The running-all-day guest is the higher-risk comparison. | Menno Drescher | `HYP-mxc-021`. Compare one paused day with one always-on day. No exposure measurement exists yet. |
| `BEN-12` Discard and reproduce | Two discards, then the parent of the next session | Path A removes the whole Hyper-V guest. Path B removes only the `.avhdx`. In both, the next session is reproduced from the approved production image and does not inherit the previous session. | Menno Drescher | `HYP-mxc-022`. Check both paths. This stays open while `BEN-08` is still waiting on a finished production bake. |

No benefit in this register is a currency amount, a density multiple, or a license saving. [Business-Case.md](Business-Case.md) records why.

---

## Realization plan

Check the operational benefits in this order. A later check is meaningless if an earlier one has already failed.

1. **Pause cost (`BEN-01`).** Confirm a paused guest still holds RAM, still has its image disks allocated, and charges 0.0% CPU. Take the first GPU reading in the same pass. If CPU is not zero, or the image disks are gone, stop. The rest of the case assumed an idle guest is free of processor cost and still occupies its disks.
2. **Wake (`BEN-02`, `BEN-03`).** One cold wake from `Paused`, timed to unpause and to the first byte, with the HTTP status recorded. Warm repeats do not replace this check.
3. **Route (`BEN-04`).** One ADPA path, one SIDPA path, and one catalogued listen port.
4. **Isolation (`BEN-05`) and sign-in (`BEN-06`).** Subsystem calls, then one username, password, and second-factor attempt against a guest that starts paused. Name the second factor before calling `BEN-06` passed.
5. **Clean session and clean image (`BEN-07`, `BEN-08`).** Write a guest file, release, confirm it is gone and the parent hash matches. Inventory the production image when a bake exists. Until that bake exists, `BEN-08` stays open.
6. **Burst and footprint (`BEN-09`, `BEN-10`).** Lease the ready guest, time the refill, read `/health`, then measure paused RAM after release. State the surge threshold used. State whether the RAM target is 1.0–1.2 GB.

`HYP-mxc-015` through `HYP-mxc-020` are reviewed as hypotheses. They are not on this realization plan. Add a benefit only after one of them is kept and given a measure.

The charter, when it is written, takes this register as an input. It does not invent a seventh money benefit the spark and the ideation document never stated.
