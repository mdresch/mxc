---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating / Planning"
pmbok_process: "4.1 Develop Project Charter"
lifecycle_stage: "Stage 2 (Objective)"
governance_policy: "approve-charter"
inputs:
  - "Project-Charter.md"
  - "Benefits-Statement.md"
  - "Business-Case.md"
  - "Ideation-Document.md"
process: "Track unresolved assumptions and decisions that affect authorization, planning, and benefit verification"
outputs:
  - "Assumption-Log.md"
status: "Open — maintained with the approved Charter"
---

# Assumption Log — MXC Hyper-V for ADPA / SIDPA

> **Source:** [Approved Project Charter](Project-Charter.md)
> **Status:** Open items remain unresolved; this log does not change approved scope or acceptance criteria.

| ID | Assumption / open decision | Why it matters | Owner | Status / resolution evidence |
|---|---|---|---|---|
| A-01 | Individual members and standing approval process for the Steering Committee roles are not recorded. | Establishes independent authority for future charter changes and spending above USD 25,000. | Menno Drescher / Steering Committee | Open; record names, approval process, and decision evidence when confirmed. |
| A-02 | The surge target is above 5 requests/second, but its measurement window is not specified; the source documents also record a separate 10-or-more requests/second over 5 seconds threshold. | A test cannot be reproducible or pass/fail until the observation window and conflicting threshold are reconciled. | Menno Drescher | Open; approved test definition required. |
| A-03 | The Charter and Benefits Statement select a paused footprint under 700 MB, while the Ideation Document and Business Case state about 1.0–1.2 GB. | Capacity planning and benefit acceptance would be invalid if the target is inconsistent or unmeasured. | Menno Drescher | Open; reconcile source documents and measure the agreed criterion. |
| A-04 | The production ADPA image and its readiness evidence are not complete. | Production-image, toolchain-separation, and reproduce-after-discard benefits depend on an approved image. | Menno Drescher / technical owner TBD | Open; record image identifier, bake completion, and approval evidence. |
| A-05 | Mobile App Verification is the selected second-factor method; its product and integration details are unspecified. | Sign-in verification cannot be scripted or fully accepted without implementation details. | Menno Drescher / technical owner TBD | Open; record the implementation and test evidence. |
| A-06 | The USD 25,000 amount is the Project Manager's spending authority, not a total project budget. No total budget, host count, license price, ROI, or payback is established. | Financial forecasting and procurement commitments cannot be inferred from the authority threshold. | Menno Drescher | Open; provide a separately approved total budget or retain the explicit no-total-budget status. |
| A-07 | Technical reviewers, test owners, additional project-team assignments, resource availability, host capacity, and operational cadence are not specified. | Resource, acceptance, communications, schedule, and cost plans cannot claim commitments without them. | Menno Drescher | Open; assign owners and record evidence before execution commitments. |
| A-08 | Existing downstream artifacts reference `PMP-BL-v1.0.0`, but no canonical approval record establishes it as an approved PMP baseline. | The Scope Foundation Pack blocks baseline roll-up pending canonical PMP evidence. | Menno Drescher / Steering Committee | Open; reconcile lifecycle records and approval evidence before pack roll-up. |

## Maintenance

Update an item only when an authorized decision or verifiable evidence resolves it. Record the decision-maker, date, evidence link, and affected documents. Do not silently convert assumptions into facts or use this log as approval for scope, schedule, cost, or technical requirements.
