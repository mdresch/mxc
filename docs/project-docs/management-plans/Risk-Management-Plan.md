---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "11.1 Risk Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Business-Case.md"
  - "../Benefits-Statement.md"
  - "../Assumption-Log.md"
process: "Record, monitor, and respond to project risks using evidence-based dispositions"
outputs:
  - "Risk-Management-Plan.md"
status: "Draft — pending review and approve-pmp"
---

# Risk Management Plan — MXC Hyper-V for ADPA / SIDPA

> **Status:** Draft for review. The Charter provides known open items but no probability/impact scoring scale or risk-review cadence. `approve-subsidiary-plan` has not been run.

## Risk process

Record each risk with an ID, cause/event/consequence, affected objective, evidence/source, owner, response, trigger, status, and review history. Do not assign numerical probability, impact, or overall ratings without an agreed scale and evidence. Review a risk when its source changes, a trigger occurs, a test fails, or a decision is requested. The Project Manager coordinates the register; technical risk owners remain to be assigned.

## Initial risk register

| ID | Risk / consequence | Response or next action | Owner / status |
|---|---|---|---|
| R-01 | Conflicting paused-RAM targets could cause invalid capacity assumptions or a false acceptance result. | Reconcile under-700 MB with the 1.0–1.2 GB figures, then measure under controlled conditions. | Project Manager / open |
| R-02 | The surge threshold's measurement window is undefined; pool behavior cannot be assessed consistently. | Define and record the observation window before testing. | Project Manager / open |
| R-03 | Production image is not complete; image cleanliness and reproduce-after-discard benefits cannot yet be accepted. | Keep dependent benefits open until the approved production image and bake evidence exist. | Project Manager / open |
| R-04 | Paused guests keep RAM and image disks allocated; host capacity and disk needs may constrain pool size. | Measure resource use and size only after requirements and allocations are available. | Project Manager / open |
| R-05 | GPU use has no prior measurement. | Capture the first host GPU reading as a test, not as confirmation. | Test owner TBD / open |
| R-06 | Mobile App Verification is selected, but product/integration details are not specified. | Identify implementation details before scripting or accepting the sign-in benefit. | Product/technical owner TBD / open |
| R-07 | The PM is also sponsor; individual Steering Committee members and routine approval process are not recorded. | Record committee members and decision process; retain independent approval for charter and spending above USD 25,000. | Project Manager / open |
| R-08 | No total project budget, host count, license price, or currency ROI is established. | Do not claim financial savings or commit beyond USD 25,000 without committee approval and supporting evidence. | Project Manager / open |

## Response, escalation, and approval

Preserve failed tests and unresolved assumptions as risks until evidence supports closure. Changes to approved scope or acceptance criteria require the applicable human governance approval. Spending above USD 25,000 requires Steering Committee approval before commitment. Do not invent escalation timelines, tolerances, or contingency values. This plan remains a draft pending `approve-pmp`.
