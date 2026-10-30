---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Business Documents / Economic Feasibility Analysis"
lifecycle_stage: "Stage 4 (Benefit)"
governance_policy: "approve-business-case"
inputs:
  - "Ideation-Document.md (Hypotheses)"
  - "Organizational strategic goals"
process: "Evaluate economic viability, ROI expectations, investment limits, and business alternatives"
outputs:
  - "Business-Case.md (Input to Benefits Statement & Project Charter)"
---

# Business Case — Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

> **PMBOK 8 Process:** `Business Documents / Economic Feasibility Analysis` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 4 (Benefit)`  
> **Inputs:** [Ideation-Document.md](Ideation-Document.md) (`HYP-mxc-001` through `HYP-mxc-020`), [Spark-Capture.md](Spark-Capture.md)  
> **Process:** Evaluate economic viability, ROI expectations, investment limits, and business alternatives  
> **Outputs:** Business-Case.md (Input to [Benefits-Statement.md](Benefits-Statement.md) and the charter)

**Source:** [Ideation-Document.md](Ideation-Document.md), [Spark-Capture.md](Spark-Capture.md)  
**Date:** 2026-10-29  
**Project Name:** MXC Hyper-V for ADPA / SIDPA  
**Project Description:** Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes  
**Captured by:** Menno Drescher  
**Investment limit:** Not set. Neither the spark nor the ideation document states a budget, a host count, or a license price.  
**Status:** Approved. `approve-business-case` accepted `approve_business_case` on 2026-10-29 (policy `91a33a4f-7d22-43e1-85ff-51026f350df0`). The approval covers the operational case as written. It does not set an investment limit or a currency ROI.

---

## Expected value premise

Every benefit below is tied to a hypothesis. Where the spark or the ideation document does not supply a number, this case does not invent one.

| Hypothesis | Value premise | What can be targeted now |
|---|---|---|
| `HYP-mxc-001`, `HYP-mxc-007` | A paused guest costs no CPU and no GPU. Its RAM stays resident, and the disk space for its images stays allocated. Idle machines stop burning processor time. They do not stop occupying disk. | 0.0% CPU and 0.0% GPU while `Paused`. RAM stays assigned. Parent VHDX and any `.avhdx` stay allocated. |
| `HYP-mxc-002`, `HYP-mxc-003`, `HYP-mxc-010` | Callers do not wait through a cold boot and do not see a gateway error caused by the wake. | `Resume-VM` ≤ 300 ms. First byte ≤ 800 ms. No HTTP 502 or 504 caused by the wake. |
| `HYP-mxc-005`, `HYP-mxc-012` | The fast path is resume from a trimmed pause, not a boot from a stopped disk. | Trim before pause. Paused footprint about 1.0–1.2 GB. A stopped guest is outside the benefit. |
| `HYP-mxc-006`, `HYP-mxc-009` | Confidential ADPA and SIDPA work keeps a dedicated Windows guest, including WMI, COM+, services, and Group Policy. | Shared-kernel containers are rejected for these workloads. |
| `HYP-mxc-008` | Username, password, and MFA meet a guest that is already awake. | Sign-in does not include a 25–45 second boot. The MFA method itself is not specified. |
| `HYP-mxc-011`, `HYP-mxc-013` | Production images stay free of developer tools, and session disk writes do not survive the session. | Toolchain absent from the production image. Session files gone after release. Egress stays on the named whitelist. |
| `HYP-mxc-014` | A burst does not fall through to a cold boot. | Ready pool refills in about 1.5 seconds. Wake clears stale database pools, reseeds randomness, and steps the clock. |
| `HYP-mxc-004` | A request reaches the image that owns it. | Path selects the pool. Listen port selects the catalogued image. These two routes are both stated and are not yet one rule. |
| `HYP-mxc-021` | A guest left closed and idle is a smaller security risk than the same guest left running. Doing nothing, and leaving it running, keeps the attack window open all day. | While `Paused`, the guest executes nothing and accepts no new session. |
| `HYP-mxc-022` | After a session, either the whole Hyper-V guest is discarded or only the `.avhdx` is discarded. The next session is reproduced from the approved production image. | Both discards are valid. The next session's parent is the approved production image. |
| `HYP-mxc-015` through `HYP-mxc-020` | Later research. | No benefit is claimed from these until one is reviewed and kept. |

Money value is not in this table. Density multiples, license savings, and power cost appear in later architecture notes. The spark explicitly left pool size and cost out of Stage 1. The ideation document did not add a cost hypothesis. This case will not promote those figures into an ROI.

---

## Scope

In scope for the value this case claims:

- ADPA and SIDPA on Windows Server 2025 guests that sleep between requests and wake on an HTTPS or other web request.
- Username and password, then MFA, on that same wake.
- Hardware isolation rather than a shared kernel.
- A production image separate from the developer image, session disk discard, and the egress whitelist named in `HYP-mxc-013`.

Out of scope for this case, because the upstream documents do not settle them:

- A budget, a payback period, or a host-purchase plan.
- `HYP-mxc-015` through `HYP-mxc-020` (micro-VM size, long-lived streams, signed images, a disk-saved tier, memory scratch disks, and forecast pre-warm).
- Choosing between a surge threshold of 5 requests per second and 10 requests per second. `HYP-mxc-014` records both.

---

## Risks

| Risk | Why the upstream documents leave it open |
|---|---|
| The money case cannot be approved | No investment limit, no rate, no license price, and no agreed density benefit in the spark or the ideation document. |
| Two memory targets | `HYP-mxc-012` carries both "about 1.0–1.2 GB" and a lessons-learned trim under 700 MB. A single savings claim cannot use both. |
| Two surge thresholds | `HYP-mxc-014` carries both above 5 requests per second and at least 10. Capacity planning cannot pick one yet. |
| Sign-in benefit is only partly specified | `HYP-mxc-008` requires username, password, and a second factor. It does not name the factor. Kerberos on port 88 is the directory path the suite already allows. |
| Production image is not finished | `HYP-mxc-011` records the production bake as still active and the ADPA catalog entry as planned. The attack-surface benefit is not yet available to claim as realized. |
| Paused RAM is a standing cost | `HYP-mxc-007` keeps memory assigned while CPU and GPU sit at zero. Hosts must hold that RAM. The case does not say how many paused guests a host can carry. |
| Image disk is a standing cost | `HYP-mxc-001` and `HYP-mxc-007` keep the parent image and any `.avhdx` allocated while the guest is paused. Zero CPU does not free that disk. The catalog shows a 10.88 GB golden parent and a 39.25 GB developer image, each capped at 64 GB. A paused-guest total is not measured. |
| Idle trim may not be the footprint that pauses | `HYP-mxc-012` notes that release restores the checkpoint and then suspends. The paused size is the checkpoint size when that restore succeeds. |
| GPU is unmeasured | `HYP-mxc-007` states 0.0% GPU. No GPU reading exists in the suite. |

---

## Example: 1, 2, or 3 images on standby

`HYP-mxc-001` and `HYP-mxc-007` still apply: each standby guest uses 0.0% CPU and 0.0% GPU, keeps about 1.0–1.2 GB of RAM, and keeps its disks. The suite places those disks on NVMe SSD. The same gigabytes apply if the copies sit on another fast disk. This example uses the catalog. It is not a measured paused-guest total.

Each copy below is one full image file. A shared parent plus a per-guest `.avhdx` would store the parent once. The catalog does not give a size for that `.avhdx`, so it is not added here.

**Golden parent, `winserv2025-golden.vhdx`, current file 10.88 GB, cap 64 GB**

| Standby images | Disk at current size | Disk if each copy is allowed to reach 64 GB | RAM while paused |
|---|---|---|---|
| 1 | 10.88 GB | 64 GB | about 1.0–1.2 GB |
| 2 | 21.76 GB | 128 GB | about 2.0–2.4 GB |
| 3 | 32.64 GB | 192 GB | about 3.0–3.6 GB |

**Developer image, `winserv2025-mxc-dev.vhdx`, current file 39.25 GB, cap 64 GB**

| Standby images | Disk at current size | Disk if each copy is allowed to reach 64 GB | RAM while paused |
|---|---|---|---|
| 1 | 39.25 GB | 64 GB | about 1.0–1.2 GB |
| 2 | 78.50 GB | 128 GB | about 2.0–2.4 GB |
| 3 | 117.75 GB | 192 GB | about 3.0–3.6 GB |

The operator guide asks for at least 50 GB free on the NVMe tier. Three golden parents at today's 10.88 GB file size fit under that. Two developer images at 39.25 GB do not. The production ADPA and SIDPA images are still planned, each with a 64 GB cap and no current file size, so they are not in these tables.

---

## Alternatives considered

These are the business alternatives named in the spark. They are not new designs.

1. **Leave the Windows Server running.** The next request is fast. CPU, memory, and licenses are paid while nobody is calling. Rejected as the default if `HYP-mxc-001` and `HYP-mxc-007` hold.
2. **Turn the server off.** Idle cost stops. The next caller waits through a boot the spark places between 14 and 45 seconds, long enough for webhooks to time out. Rejected if `HYP-mxc-002` and `HYP-mxc-003` hold.
3. **Use a shared-kernel container.** Start-up is quick. The spark and `HYP-mxc-006` reject it for confidential records and for Windows subsystems named in `HYP-mxc-009`.

The recommended alternative is the paused guest: resident in RAM, no CPU and no GPU while paused, request held, guest resumed, sign-in and work served without a cold boot. That recommendation stands only for the operational benefits. It does not yet stand as a cheaper option in currency, because that comparison was never written.

---

## How the spark and the ideation document held up

They held up for the operational case. The trilemma, the wake ceilings, the paused guest, the discard of session disks, and the rejection of a shared kernel are all stated as hypotheses with a way to fail them. A benefits statement can target those without inventing a metric.

They did not hold up for an economic case. There is no investment limit, no owner for a money benefit, and no hypothesis for density or license savings. The ideation document is also carrying research items (`HYP-mxc-015` through `HYP-mxc-020`) and two unresolved number pairs (memory footprint, surge threshold). Those must stay out of the benefits that this case asks anyone to realize.

---

## Before the next document

[Benefits-Statement.md](Benefits-Statement.md) is the charter input. It is drafted with this case. The charter comes after both, not before.
