---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "4.1 Develop Project Charter"
lifecycle_stage: "Stage 2 (Objective)"
governance_policy: "approve-charter"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
process: "Formally authorize the project, establish sponsor authority, and define measurable objectives"
outputs:
  - "Project-Charter.md"
  - "Assumption Log"
status: "Approved"
---

# Project Charter — MXC Hyper-V for ADPA / SIDPA

> **PMBOK 8 Process:** `4.1 Develop Project Charter` (Initiating)
> **Governance Policy:** `approve-charter` | **Lifecycle Stage:** `Stage 2 (Objective)`
> **Status:** Approved by the Steering Committee on 2026-10-30; individual member names are not recorded.

- **Project description:** Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes
- **Prepared from:** [Spark Capture](Spark-Capture.md), [Ideation Document](Ideation-Document.md), [Business Case](Business-Case.md), and [Benefits Statement](Benefits-Statement.md)
- **Business Case status:** Approved on 2026-10-29 for the operational case. It does not establish a budget or currency ROI.
- **Benefits Statement status:** Draft.

## Executive summary

The project will evaluate and deliver a just-in-time Hyper-V sandbox model for ADPA and SIDPA: Windows Server 2025 guests that can remain paused between requests, resume to serve incoming work without a cold boot, and isolate confidential workloads from a shared host kernel. Sessions are intended to leave no residual guest changes, and production images are to remain separate from developer images.

The expected value in the approved Business Case is operational. It does not claim currency savings, ROI, or payback. The success measures below are targets to test, not verified outcomes.

## Leadership and investment authority

| Role or control | Charter record |
|---|---|
| Project sponsor | Menno Drescher |
| Project manager | Menno Drescher (same person holding both roles) |
| Operational benefit owner | Menno Drescher, as recorded in the Benefits Statement |
| PM spending authority | USD 25,000 |
| Spending above the PM authority | Requires Steering Committee approval before commitment |

The total project budget is not specified. The Steering Committee comprises the Sponsor, CFO, Finance Controller, IT Engineering, IT Analysis, HR, and Learning and Development; individual member names and the standing approval process are not recorded. Because Menno Drescher holds both sponsor and project manager roles, the committee provides independent approval for this charter and for spending above USD 25,000; Menno cannot approve either alone. The committee's approval of this charter was reported on 2026-10-30. This charter does not establish a currency ROI or project-wide budget allocation.

## Purpose and authorization

The project purpose is to evaluate and deliver the just-in-time Hyper-V sandbox model described above for ADPA and SIDPA. The Steering Committee approved this charter on 2026-10-30, authorizing the project within the scope and spending authority stated here.

The operational case is recorded in the approved Business Case. The targets below are proposed measures of success, not claims that the benefits have already been achieved. The Ideation hypotheses remain `Formulated` unless and until their stated tests produce and classify results.

## Success criteria

The following criteria are traced to the Benefits Statement. Values described as targets are to be tested; they are not verified results.

| Benefit | Proposed success measure |
|---|---|
| `BEN-01` Idle processor and graphics | A `Paused` guest uses 0.0% host CPU and 0.0% GPU while its RAM remains assigned and its parent VHDX and any `.avhdx` remain allocated. No GPU measurement is yet recorded. |
| `BEN-02` Wake without a cold boot | From a request arriving for a paused guest, `Resume-VM` completes in ≤ 300 ms and the first response byte arrives in ≤ 800 ms. A warm request alone does not satisfy this measure. |
| `BEN-03` No wake-caused gateway failure | A wake does not cause HTTP 502 or 504. A saturation timeout returning 503 is a separate case. |
| `BEN-04` Request reaches its owning image | `/api/v1/adpa` selects `prod-adpa`; `/api/v1/sidpa` selects `prod-sidpa`; catalogued listener ports `:8090`, `:8091`, and `:8092` select their registered images; the guest service port is `:8080`. Path-to-pool and listener-port-to-image are distinct routing checks. |
| `BEN-05` Windows work stays on its own guest | WMI, COM+, a Windows service, and Group Policy work in the Generation 2 Hyper-V guest and fail or are unsupported in the shared-kernel container comparison. |
| `BEN-06` Sign-in does not wait on boot | Username/password followed by Mobile App Verification succeeds against a guest that started paused without a 25–45 second cold boot in the user-visible wait. The guest clock is aligned before accepting sign-in. |
| `BEN-07` Session residue does not remain | A session-written file is gone after release, the parent image hash is unchanged, public internet egress is denied, and the named approved internal egress ports are allowed: SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88`. |
| `BEN-08` Production image is not a developer image | The production image contains no Scoop, cargo, git, or compiler toolchain, and `baseline-hot-ready` is captured after a warm-up request. The production bake is still active, so this benefit is not yet realized. |
| `BEN-09` A burst does not cold-boot the next caller | At a surge above 5 requests per second, a replacement standby guest is ready in about 1.5 seconds; health reports entropy reseeded, clock synced, and database pools cleared; surplus guests leave `ActiveRunning` after 300 seconds with no open requests. The surge measurement window remains open. |
| `BEN-10` Paused size is the trimmed checkpoint | The selected target is under 700 MB of host RAM per paused guest. The Benefits Statement now reflects this target; the Ideation Document and Business Case still record about 1.0–1.2 GB and must be reconciled before baselining the benefit. |
| `BEN-11` Closed idle guest | While paused, the guest does not accept a direct connection and a new session starts only after resume. Compare a paused day with an always-on day before claiming the lower-risk benefit. |
| `BEN-12` Discard and reproduce | Test both whole-guest discard and `.avhdx` discard. In either path, the next session is reproduced from the approved production image and does not inherit the prior session. |

## High-level scope and constraints

**In scope**

- ADPA and SIDPA workloads on Windows Server 2025 Hyper-V guests that are idle between requests.
- Holding and routing incoming web requests, resuming a paused guest, and serving work without a cold boot.
- Dedicated guest-kernel isolation rather than a shared-kernel container for the named confidential workloads.
- Username/password and a second-factor sign-in flow on the wake path.
- A production image separate from developer tooling, transient session changes, and the egress controls listed under `BEN-07`.
- Testing and reporting the operational success criteria above.

**Out of scope for this authorization**

- A currency-based ROI, payback period, total project budget, host-purchase plan, or license-savings claim; no such figures are established by the source documents.
- Research hypotheses `HYP-mxc-015` through `HYP-mxc-020` (micro-VM footprint, long-lived streams, signed images, a disk-saved tier, memory scratch disks, and forecast pre-warming).
- Choosing a different surge threshold; this charter selects above 5 requests per second. The source documents also record a separate 10-or-more-requests-per-second-over-5-seconds figure.

**Constraints and dependencies**

- Paused guests retain assigned RAM and allocated image disks even when CPU and GPU are at zero; host capacity and disk capacity therefore remain necessary.
- The dedicated production ADPA image is not yet complete. Criteria depending on an approved production image cannot be accepted until it exists.
- The Benefits Statement now reflects the selected under-700 MB target; the Ideation Document and Business Case retain the earlier 1.0–1.2 GB target and remain to be reconciled. The surge measurement window is not specified.
- The Ideation hypotheses are formulated claims awaiting empirical classification; implementation notes or prior reported observations do not substitute for the tests specified in the Benefits Statement.

## Stakeholders and governance

| Stakeholder or role | Responsibility / current record |
|---|---|
| Menno Drescher — Project Sponsor | Sponsor authority for the project; did not act as the independent approver because Menno also holds the Project Manager role. |
| Menno Drescher — Project Manager | Manages the project within the USD 25,000 spending authority; obtains Steering Committee approval for amounts above it before commitment. |
| Menno Drescher — Operational Benefit Owner | Named in the Benefits Statement for operational benefit checks. |
| Steering Committee | Sponsor, CFO, Finance Controller, IT Engineering, IT Analysis, HR, and Learning and Development. Approved this charter on 2026-10-30 and approves spending above USD 25,000; individual member names and the standing approval process are not recorded. |

No additional project team, technical lead, or stakeholder assignments are established in the source documents.

## High-level milestone and verification sequence

No delivery dates or duration estimates are authorized. The Benefits Statement gives this order for checking benefits; it is a verification sequence, not a project schedule:

1. Confirm paused-state resource behavior (`BEN-01`).
2. Measure wake time, first byte, and wake-caused HTTP status (`BEN-02`, `BEN-03`).
3. Test both routing behaviors (`BEN-04`).
4. Test guest isolation and sign-in (`BEN-05`, `BEN-06`).
5. Test clean-session behavior and the production image (`BEN-07`, `BEN-08`).
6. Test pool refill and paused memory footprint (`BEN-09`, `BEN-10`).

## High-level risks

| Risk | Current status |
|---|---|
| The economic case cannot establish ROI, payback, or total cost because no total budget, license price, or host count is given. | Open; PM spending authority is USD 25,000. |
| The selected under-700 MB RAM target differs from the 1.0–1.2 GB figures in the Ideation Document and Business Case. | Charter and Benefits Statement select under 700 MB; remaining source reconciliation is open. |
| The surge target has no measurement window, and the source documents also record a different threshold. | Charter selects above 5 requests per second; measurement window remains open. |
| The production image is not complete. | Open; dependent benefits cannot yet be accepted. |
| Paused guests retain RAM and image disks even while CPU and GPU are at zero. | Capacity impact is not quantified in the source documents. |
| No GPU reading is recorded. | Must be measured before claiming `BEN-01` achieved. |

## Assumptions and open items

1. Assign individuals to the identified Steering Committee roles and record the committee's approval process for the charter and amounts above USD 25,000.
2. Define the measurement window for the above-5-requests-per-second surge test.
3. Reconcile the under-700 MB target with the 1.0–1.2 GB figures remaining in the Ideation Document and Business Case before baselining `BEN-10`.
4. Record the approved production image and its readiness when the bake is complete.

Track these items in the [Assumption Log](Assumption-Log.md) until resolved. Mobile App Verification and both separate routing checks are selected. No delivery dates, schedule estimates, cost estimates, or unprovided resource commitments are authorized by this charter.

## Subsidiary management plans

This charter is not the Project Management Plan (PMP), and it does not approve any subsidiary management plan.

- **Schedule Management Plan — not yet buildable:** The charter template requires actual duration data from completed work, not estimates alone.
- **Cost Management Plan — not yet buildable:** The charter template requires Resource Allocation and Procurement outputs. The PM spending threshold is not a total project budget, and those outputs are not available in the source documents.
- Other subsidiary plans may be prepared after charter approval in the lifecycle's management-plan sequence. This charter does not invent their contents.

## Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Project Sponsor / Project Manager | Menno Drescher | Sponsor role recorded; not the independent approver | — |
| Steering Committee / independent authorizing authority | Sponsor, CFO, Finance Controller, IT Engineering, IT Analysis, HR, Learning and Development; individual names not recorded | Approved | 2026-10-30 |
