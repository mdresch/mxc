# Intent-to-Outcome Chain — PMBOK 8 Process Alignment and Closed-Loop Governance

Source of the chain concept: SocialEngage's `Intent-to-Outcome-Chain-and-TaskPolicy-Coverage.md` (Obsidian Brain wiki) and the SIDPA Project Management Lifecycle.

In enterprise software engineering and agentic governance (PMBOK 8 / SIDPA), every stage that yields a documented artifact requires a formal Bayesian validation gate. We start with a **Spark** and systematically trace intent through execution, verification, governance amendment, behavioral adaptation, and back to refined intent—closing the complete development lifecycle loop.

All document-approval policies operate under `DecisionAuthority.FULL` using multi-criteria Bayesian evaluation (`DecisionFrame`), with human adjudication mandated (`requires_human_approval: true`).

---

## 1. Document Authoring Sequence vs. Conceptual Ontology

There is an important distinction between the abstract conceptual trace and the **actual document build sequence**:

* **Conceptual Ontology (`traceabilityChain`):**
  $$\text{Intent} \longrightarrow \text{Objective} \longrightarrow \text{Hypothesis} \longrightarrow \text{Benefit} \longrightarrow \text{Pillars} \longrightarrow \text{Requirement} \longrightarrow \text{Project (PMP)} \longrightarrow \text{Readiness} \dots$$
* **Actual Document Authoring & Governance Sequence (PMBOK 8 / SIDPA Lifecycle):**
  ```
  1. Spark Capture (Intent — Initiating)
         │
  2. Ideation Document (Hypotheses — Initiating)
         │
  3. Business Case & Benefits Statement (Benefit — Initiating)
         │
  4. Project Charter (Objective — Initiating: 4.1 Develop Project Charter)
         │
  5. Pillars Exercise (Architectural Strategy Formulation: 5.3)
         │
  6. Technical Requirements & Design (Planning: 5.2 & 5.3 & 5.4)
     ├── High-Level Foundational ADRs (100% Pillar Coverage: 5.3)
     ├── Business Requirements Document (BRD: 5.2 Collect Requirements)
     ├── Functional Design Document (FDD: 5.3 Define Scope / Design)
     └── User Stories (Work Packages & WBS Decomposition: 5.4)
         │
  7. Subsidiary Management Plans (Scope 5.1/7.A, Schedule 6.1/7.B, Cost 7.1/7.D, Resource 9.1/7.C, Quality 8.1, etc.)
     & Integrated Project Management Plan (Planning: 4.2 Develop PMP — Baseline PMP-BL-v1.0.0)
         │
  8. Implementation Readiness Gate / Implementation Authorization Notice (Planning ➔ Executing Gate: validate-intent-foundation)
         │
  9. Deliverables (Executing: 4.3 Direct & Manage Work — implement-story)
         │
  10. Verification Evidence (Monitoring & Controlling: 8.3 Control Quality — Contract Test Suite)
         │
  11. Audit Record (Monitoring & Controlling: 8.2 Manage Quality Audits — Audit Register)
         │
  12. Actual Outcome (Monitoring & Controlling: 5.5 Validate Scope & Value Realization)
         │
  13. Observation (Monitoring & Controlling: 4.5 Monitor & Control Project Work — Telemetry Logs)
         │
  14. Insight (Monitoring & Controlling: 4.4 Manage Project Knowledge — Synthesis)
         │
  15. Lesson Learned (Monitoring & Controlling: 4.4 Manage Project Knowledge — Lessons Learned Register)
         │
  16. Governance Change (Monitoring & Controlling: 4.6 Integrated Change Control)
         │
  17. Adaptation Plan (Adaptive Closing / Feedback: Tailoring PMP Updates)
         │
  18. Intent Refinement (Closing: 4.7 Close Phase & Strategic Feedback to Spark)
  ```

---

## 2. Complete 18-Stage Coverage Matrix (PMBOK 8 Process & Second Brain Tooling Mapping)

| # | Chain Stage | PMBOK 8 Process Group | Governed Document Artifact | Assigned TaskPolicy | Second Brain Tooling & Scripts | Authority & Decision Shape | Lifecycle Role & IPO |
|---|---|---|---|---|---|---|---|
| 1 | **Intent** | **Initiating** | `Spark-Capture.md`<br>`Ideation-Document.md` | `approve-ideation` | `run-lifecycle-pipeline.mjs` | `FULL` (3 actions) | **Starts with a Spark.** Inputs: Trigger event / strategic driver. Process: Validate intent. Output: Approved Ideation. |
| 2 | **Objective** | **Initiating** | `Project-Charter.md` | `approve-charter` | `query-knowledge-graph.mjs` | `FULL` (3 actions) | Inputs: Business Case & Benefits. Process: Authorize project & assign sponsor. Output: Project Charter. |
| 3 | **Hypothesis** | **Initiating** | `Ideation-Document.md`<br>(`HYP-*.md`) | `classify-hypothesis-status` | `query-knowledge-graph.mjs` | `FULL` (7 actions) | Inputs: Design assumptions & test logs. Process: Evaluate empirical evidence. Output: Validated / testing status. |
| 4 | **Benefit** | **Initiating** | `Business-Case.md`<br>`Benefits-Statement.md` | `approve-business-case` | `run-lifecycle-pipeline.mjs` | `FULL` (3 actions) | Inputs: Hypotheses & ROI premise. Process: Validate economics. Output: Benefits Statement (Input to Charter). |
| 5 | **Pillars & Architecture** | **Planning** | `PILLARS-EXERCISE.md`<br>High-Level `ADR-*.md` | `approve-adr` | `ground-adrs-to-concepts.mjs` | `FULL` (3 actions) | Inputs: Project Charter & Hypotheses. Process: Decompose Charter into pillars; draft ADRs providing 100% pillar coverage. Output: Approved Pillars & ADRs. |
| 6 | **Requirement** | **Planning** | • `ADR-*.md`<br>• `BRD-*.md`<br>• `FDD-*.md`<br>• `user-stories/*.md` | • `approve-adr`<br>• `approve-brd`<br>• `approve-fdd`<br>• `approve-user-stories` | `vault-ingestion.mjs`<br>`ground-adrs-to-concepts.mjs` | `FULL` (3 actions each) | Inputs: Approved Pillars & Architecture. Process: Business requirements, functional specifications, and atomic User Stories. **Output: Approved technical requirements and work packages.** |
| 7 | **Project (PMP & Baselines)** | **Planning** | `Project-Management-Plan.md`<br>& Subsidiary Plans (5.1–13.2)<br>Foundation Packs (7.A–7.D) | • `approve-subsidiary-plan`<br>• `approve-pmp` | `orchestrate_pmbok.py --mode full` | `FULL` (3 actions each) | Inputs: Stage 6 Requirements, WBS & Foundation Packs (Scope 7.A, Schedule 7.B, Resource 7.C, Cost 7.D). Process: Ground duration/cost/scope baselines and integrate plans. Output: Approved PMP (`PMP-BL-vX.Y.Z`). |
| 8 | **Implementation Readiness** | **Planning ➔ Executing** | `Stage-8-Implementation-Authorization-Notice.md`<br>Epic Readiness Check | `validate-intent-foundation` | `run-lifecycle-pipeline.mjs` | `FULL` (3 actions: accept, reject, flag) | **Focus:** Certifies that tests, environment, criteria readiness, and planning artifacts are reconciled before developer begins implementation. Formally informs all parties that PMP is approved and authorizes staffing, procurement, and execution. Output: Provisioned git worktree. |
| 9 | **Deliverable** | **Executing** | Source Code & Release Artifacts | Direct Execution | `.claude/skills/implement-story` | Code-First TDD | Inputs: Approved stories & acceptance criteria. Process: TDD / contract-first build. Output: Executable code deliverable. |
| 10 | **Verification Evidence** | **Monitoring & Controlling** | Contract Tests & Execution Logs | Executable Test Suite | `.claude/skills/heal-contract-failure` | 4-Ring Quality Gate | Inputs: Code deliverable & contract tests. Process: Execute test suite. Output: Verification evidence report (pytest / vitest). |
| 11 | **Audit Record** | **Monitoring & Controlling** | `Audit-Register.md`<br>`Audit-Finding.md` | `approve-audit-record` | `run-lifecycle-pipeline.mjs` | `FULL` (3 actions) | Inputs: Deliverables & verification logs. Process: Audit architectural conformance. Output: Approved Audit Register entries. |
| 12 | **Actual Outcome** | **Monitoring & Controlling** | Post-Delivery Impact Assessment | Empirical Observation | `analyze-graph.mjs` | Baseline Comparison | Inputs: Production telemetry & Benefits Statement. Process: Compare realized vs expected value. Output: Impact deltas. |
| 13 | **Observation** | **Monitoring & Controlling** | Telemetry Logs & Gotchas (`OBS-*.md`) | Second Brain Ingestion | `heal-brain.mjs`<br>`diagnose-broken-links.mjs` | Raw Input | Inputs: Runtime telemetry & review findings. Process: Record raw telemetry. Output: Unfiltered observation log. Path: §3.2. |
| 14 | **Insight** | **Monitoring & Controlling** | Synthesized Technical Findings (`INSIGHT-*.md`) | `synthesis-validator.mjs` | `synthesis-validator.mjs` | `FULL` (trust existing, supersede, flag) | Inputs: Observation logs. Process: Synthesize causal significance. Output: Resolved insight node. Path: §3.2. |
| 15 | **Lesson Learned** | **Monitoring & Controlling** | Formalized Knowledge (`LL-*.md`, Register) | `resolve-kb-conflict` | `heal-brain.mjs` | `FULL` (trust existing, supersede, flag) | Inputs: Verified insights. Process: Crystallize actionable knowledge. Output: Formalized Lessons Learned register. Path: §3.2. |
| 16 | **Governance Change** | **Monitoring & Controlling** | Governance Amendments & Diffs (`GC-*.md`) | • `classify-diff-type`<br>• `escalate-diff-response` | `compile-ontology-graph.mjs` | Paired Pipeline: `FULL` / `LOW` | Inputs: Lessons learned (`evidence_basis: execution`) or Stage 7-8 baseline findings (`evidence_basis: design_time`, §3.1) & proposed diffs. Process: Semantic classification & escalation bandit. Output: Governed baseline update. |
| 17 | **Adaptation Plan** | **Closing / Adaptive Feedback** | `Adaptation-Plan.md` | `approve-adaptation-plan` | `orchestrate_pmbok.py --mode adapt` | `FULL` (3 actions) | Inputs: Validated Stage 16 governance change & realized outcomes from executed work (design-time changes go Stage 16 → Stage 6 directly, §3.1). Process: Tailor PMP subsidiary plans via Governance Change Impact Matrix. Output: Impacted plan list. |
| 18 | **Intent Refinement** | **Closing / Strategic Feedback** | `Intent-Refinement-Proposal.md` | `approve-intent-refinement` | `build-18-stage-canvas.mjs`<br>`run-lifecycle-pipeline.mjs` | `FULL` (3 actions) | Inputs: Accepted Stage 17 adaptations & phase review. Process: Strategic review of original Intent. Output: **Catalyst for Phase N+1 Spark Capture**. |

---

## 3. The Continuous Adaptation & PMP Feedback Cycle

The approved baseline has **two** routes back, kept apart. This section is the **execution loop**: the trigger is evidence from executed work (Stage 9-15 deliverables, tests, audits, observed outcomes, insights and lessons learned) and the route is Stage 16 → Stage 17 → Stage 6. Section 3.1 is the **design-time loop**, for defects found before anything is built.

When an operational gap, audit finding, or governance amendment occurs:
```mermaid
flowchart TD
    SPARK["Stage 1: Intent<br/>Spark-Capture.md & Ideation-Document.md"] --> CHARTER["Stage 2: Objective & Charter<br/>Project-Charter.md"]
    CHARTER --> PIL["Stage 5: Pillars Exercise<br/>PILLARS-EXERCISE.md"]
    PIL --> ADR["Stage 6a: High-Level ADRs (100% Pillar Coverage)<br/>approve-adr"]
    ADR --> BRD["Stage 6b: Business Requirements (BRD)<br/>approve-brd"]
    BRD --> FDD["Stage 6c: Functional Design (FDD)<br/>approve-fdd"]
    FDD --> US["Stage 6d: User Stories (Work Packages)<br/>approve-user-stories"]
    US -->|"Grounds duration, story points, resources, cost"| SUB["Stage 7a: Subsidiary Plans & Foundation Packs<br/>Scope (7.A), Schedule (7.B), Resource (7.C), Cost (7.D)<br/>approve-subsidiary-plan"]
    SUB -->|"Integrates triple baselines"| PMP["Stage 7b: Integrated Project Management Plan<br/>Project-Management-Plan.md (PMP-BL-v1.0.0)<br/>approve-pmp"]
    PMP --> WP["Stage 8: Implementation Readiness Gate<br/>(Implementation Authorization Notice)<br/>validate-intent-foundation"]
    WP --> DEL["Stage 9-10: Deliverables & Verification<br/>implement-story & test suite"]
    DEL --> AUD["Stage 11: Audit Record<br/>approve-audit-record"]
    AUD --> KB["Stage 13-15: Outcomes, Insights & Lessons Learned<br/>resolve-kb-conflict"]
    KB --> GOV["Stage 16: Governance Change<br/>classify-diff-type & escalate-diff-response"]
    GOV --> ADAPT["Stage 17: Adaptation Plan<br/>approve-adaptation-plan"]
    ADAPT -->|"Tailored updates to impacted subsidiary plans"| SUB
    ADAPT --> REFINE["Stage 18: Intent Refinement<br/>approve-intent-refinement"]
    REFINE -->|"Seeds Phase N+1"| SPARK
```

### 3.1 The design-time loop (Stages 7-8 → Stage 16 → Stage 6)

Writing and reviewing Stage 7 requirements, or checking Stage 8 readiness, can turn up defects in the *approved baseline* before anything is built: a critical path that contradicts a directive, a circular gate, a lapsed milestone, accepted ADRs that imply plan updates the plans lack, ADRs that conflict with each other. The execution loop above is the wrong route for these: there is no Stage 9-15 evidence yet, so there is nothing for a Stage 17 Adaptation Plan to adapt. They take a second route, **alongside the execution loop and not replacing it**:

```mermaid
flowchart TD
    R["Stage 7 review / Stage 8 readiness check"] -->|"finding cites the documents"| B["BFI-NNN logged<br/>(internal working item, PMP §3.3)"]
    B --> C["Stage 16: classify-diff-type<br/>evidence_basis = design_time"]
    C --> E["escalate-diff-response<br/>(Charter approval-limit thresholds)"]
    E -->|"editorial"| ED["Apply and log"]
    E -->|"upstream ADR / BRD / FDD"| UP["Amend, then re-confirm with that document's own policy"]
    E -->|"within PM authority"| PM["PM revises the plan; the plan's own policy re-approves"]
    E -->|"Steering Committee"| BRP["PM produces a Baseline Revision Package<br/>Steering Committee approves<br/>approve-pmp records PMP-BL-v1.0.x"]
    ED --> X["Cascade check of downstream Stage 7 documents"]
    UP --> X
    PM --> X
    BRP --> X
    X -->|"re-enter the chain where the finding was raised"| R
```

**What the loop does**
1. **Capture** each baseline defect found at Stage 7 or 8 as a `BFI-NNN`, citing the documents it concerns directly. Log it in the PMP's Pending Baseline Feedback table (PMP template §3.3), not in an Adaptation Plan.
2. **Classify and route** it through the existing Stage 16 policies: `classify-diff-type` with `evidence_basis = design_time`, then `escalate-diff-response`. Editorial fixes, upstream document amendments, PM-level plan fixes and Steering-Committee-level changes are told apart there.
3. **Submit a baseline, not an amendment.** For a Steering-Committee-level item the PM produces a **Baseline Revision Package**, and the Steering Committee approves a complete revised baseline: always the revised PMP and the changed plans plus the standard set (Spark, Ideation, Business Case, Benefits Statement, Stakeholder Register); the Charter only if it is amended. `approve-pmp` records the new baseline.
4. **Cascade back.** After a change, re-check the downstream Stage 7 documents and re-enter the chain where the finding was raised.

**Guardrails**
- It fixes logic and records variance only. It adds no new durations, costs or estimated dates (`sequence-and-lessons.md` Rule #3) and invents no evidence (Rule #17).
- Human approval throughout.
- It stays separate from the execution loop: a design-time fix is never a lesson learned, never touches Stage 17, and never refines Intent (Stage 18).
- It needs no new TaskPolicy while the existing ones fit (Rule #16).
- Change-control episodes carry `evidence_basis: design_time | execution`, so policies that later learn from them do not mix the two kinds.

**Versioning.** Design-time revisions are patch increments (`PMP-BL-v1.0.x`). Minor increments (`PMP-BL-v1.1.0`) are reserved for Stage 17 adaptations from executed work. The case that surfaced the loop is in `sequence-and-lessons.md` Rule #21.

### 3.2 The Stage 13-15 knowledge path (Observation → Insight → Lesson Learned)

Stages 13-15 had a named home (the shared knowledge base) but no written path. This is the path, first written in Kayros Bay's PROP-002 (2026-10-27) and reviewed against the shared vault ontology. The vault node types are `observation`, `insight`, `lesson_learned`, `governance_change` and `adaptation`; the ids below follow the ontology's own patterns.

```mermaid
flowchart TD
    RUN["Executed work: a pipeline run, a test, a delivery, an audit"] --> OBS["Stage 13: OBS-nnnn in raw/observations<br/>status Observed · evidence = what ran, when, output"]
    OBS -->|"triage: real? repeatable? whose?"| TRI["Observed → Triaged"]
    TRI --> INS["Stage 14: INSIGHT-nnnn<br/>derived from the observation"]
    INS --> KBC{"resolve-kb-conflict<br/>does it contradict an existing node?"}
    KBC -->|"no conflict / trust_existing"| ACT["Insight Active"]
    KBC -->|"supersede"| SUP["Existing node marked superseded<br/>insight Active"]
    KBC -->|"flag"| HUM["Held for the Project Owner"]
    ACT --> LL["Stage 15: Lesson-nnnn<br/>Draft → Reviewed → Active"]
    SUP --> LL
    LL -->|"changes how the project or its tooling works"| G16["Stage 16: classify-diff-type<br/>evidence_basis = execution · escalate-diff-response"]
    G16 -->|"validated change"| A17["Stage 17: Adaptation-Plan.md entry<br/>cites the lesson · approve-adaptation-plan"]
    KBC -.->|"a note contradicts an accepted project document"| DOC["trust_existing (correct the note)<br/>or flag → BFI (§3.1)"]
```

**Stage 13, capture (no adjudication).** Record only what was seen: what ran (command, version), when, the output or file evidence and the artifact touched. No interpretation and no fix. Triage (`Observed → Triaged`) confirms it is real and reproducible; a one-off that cannot be reproduced stays `Observed`.

**Stage 14, the `resolve-kb-conflict` decision.** Does the insight contradict an existing knowledge-base node (a concept note, an earlier insight or lesson, a compiled ADR page)? `trust_existing`: the existing node stands and the insight is recorded and linked. `supersede`: the insight replaces the node, which is marked superseded, not deleted. `flag`: not decidable from the evidence; held for the Project Owner.

**Authority rule for project documents.** The knowledge base cannot supersede an accepted project document (an ADR, BRD, FDD or plan). A conflict between a note and such a document is resolved as `trust_existing` (the note is corrected) or `flag` (the project document may be wrong).

**Which route a contradiction takes.** A contradiction that is visible from the documents alone (for example a note against an accepted ADR) is a baseline feedback item, raised as a BFI and handled by §3.1. A lesson that comes from executed work and shows an accepted ADR or the baseline to be wrong is execution evidence and takes the execution route: Stage 16 (`evidence_basis: execution`), then Stage 17. A finding enters one route, never both (§3.1).

**Stage 15 to 17.** A lesson that changes how the project or its tooling works enters Stage 16 with `evidence_basis: execution`. Only a validated Stage 16 change becomes an Adaptation-Plan entry citing the lesson, approved by `approve-adaptation-plan`. A change to the shared vault's own scripts is governed in the project but lands in the vault repository.

**Ids.** Projects that share a vault allocate a range per node type, recorded in the project's own documents, so the vault's duplicate-id audit stays clean. Use the ontology's patterns (`OBS-nnnn`, `INSIGHT-nnnn`, `Lesson-nnnn`, `GOV-CHG-nnnn`, `ADAPT-nnnn`).

**Policy status.** `resolve-kb-conflict` belongs to the shared `obsidian-brain-ingestor`, not to a project's governance namespace (`sequence-and-lessons.md` Rule #19). Its three actions are kept as reference in `docs/policy-shapes/resolve-kb-conflict.NOT-INITIALIZED.actions.json`: `FULL` authority, human approval required (Rule #18), zero episodes. Nothing is automated, nothing is learned, no project-local knowledge base is built, and there is no Stage 18 shape (Rule #20). Before the first real episode, validate the frame against a deliberately wrong case (Rule #10).

---

## 4. Directory Layout in This Template

```
sidpa-template/
├── .github/
│   └── instructions/
│       ├── codacy.instructions.md
│       └── sidpa-governance-qa.instructions.md     # Universal QA directives for agents
├── docs/
│   ├── chain-coverage.md                         # This comprehensive coverage matrix
│   ├── sequence-and-lessons.md                   # Battle-tested sequence rules and empirical lessons
│   ├── root-cause-log.md                         # Policy justifications
│   ├── project-docs/
│   │   ├── Spark-Capture.template.md              # Stage 1: Intent (Initiating)
│   │   ├── Ideation-Document.template.md          # Stage 1: Intent & Stage 3: Hypotheses (Initiating)
│   │   ├── Project-Charter.template.md            # Stage 2: Objective (Initiating: 4.1)
│   │   ├── Business-Case.template.md              # Stage 4: Benefit (Initiating)
│   │   ├── Benefits-Statement.template.md         # Stage 4: Benefit (Initiating)
│   │   ├── Project-Management-Plan.template.md    # Stage 7: PMP & Integrated Baselines (Planning: 4.2)
│   │   ├── Project-Management-Plan.md             # Stage 7: Initialized PMP instance
│   │   ├── Status-Reports/
│   │   │   └── Stage-8-Implementation-Authorization-Notice.template.md # Stage 8: Implementation Authorization
│   │   ├── Adaptation-Plan.template.md            # Stage 17: Adaptation (Monitoring & Controlling / Tailoring)
│   │   ├── Intent-Refinement-Proposal.template.md # Stage 18: Intent Refinement (Closing: 4.7)
│   │   ├── Business-Requirements/
│   │   │   └── BRD-TEMPLATE.md                    # Stage 6: Requirement (Planning: 5.2/5.3)
│   │   ├── Functional-Design/
│   │   │   └── FDD-TEMPLATE.md                    # Stage 6: Requirement (Planning: 5.3)
│   │   └── management-plans/                      # Stage 7: Subsidiary Plans (5.1–13.2) & Foundation Packs
│   │       ├── Scope-Management-Plan.md
│   │       ├── Schedule-Management-Plan.md
│   │       ├── Cost-Management-Plan.md
│   │       ├── Resource-Management-Plan.md
│   │       ├── Quality-Management-Plan.md
│   │       ├── Communications-Management-Plan.md
│   │       ├── Risk-Management-Plan.md
│   │       ├── Procurement-Management-Plan.md
│   │       ├── Stakeholder-Engagement-Plan.md
│   │       ├── scope-baseline/                    # Stage 7.A Scope Foundation Pack
│   │       ├── schedule-baseline/                 # Stage 7.B Schedule Foundation Pack
│   │       ├── resource-baseline/                 # Stage 7.C Resource Foundation Pack
│   │       └── cost-baseline/                     # Stage 7.D Cost Foundation Pack
│   ├── 07-architecture/
│   │   ├── PILLARS-TEMPLATE.md                    # Stage 5: Architectural Pillars Definition
│   │   └── ADR-TEMPLATE.md                        # Stage 6: Architectural Decision Records
│   ├── user-stories/
│   │   └── EPIC-TEMPLATE.md                       # Stage 6: Work Packages & User Stories (Planning: 5.4)
│   ├── registers/
│   │   ├── Audit-Register.template.md             # Stage 11: Audit Record (PMBOK 8.2)
│   │   └── Story-Execution-Register.template.md   # Stage 9: Deliverable Tracking (PMBOK 4.3)
│   └── policy-shapes/                             # Canonical JSON action shape specifications
├── package.json                              # npm lifecycle and Second Brain runner
├── scripts/
│   ├── brain/                                # Second Brain automation & healing suite
│   │   ├── run-lifecycle-pipeline.mjs        # 18-stage master runner
│   │   ├── heal-brain.mjs                    # Referential integrity self-healing
│   │   ├── compile-ontology-graph.mjs        # Ontology compiler & loop closure check
│   │   ├── synthesis-validator.mjs           # Decision inversion & synthesis validator
│   │   ├── brain-drift-detection.mjs         # Codebase vs ontology drift monitor
│   │   ├── build-18-stage-canvas.mjs         # Interactive 2D Obsidian canvas generator
│   │   └── query-knowledge-graph.mjs         # CLI graph query engine
│   ├── init_project.py                       # Project scaffolder
│   └── orchestrate_pmbok.py                  # PMP & subsidiary plan orchestrator
└── templates/
    └── management-plans/                          # Stage 7 Foundation Pack source templates
        ├── scope-baseline/                        # Stage 7.A Scope
        ├── schedule-baseline/                     # Stage 7.B Schedule
        ├── resource-baseline/                     # Stage 7.C Resource
        └── cost-baseline/                         # Stage 7.D Cost
```

---

## 5. Governance Invariants & Baseline Versioning Rules

1. **Requirements Ground Baselines (Invariant 1):** Technical Requirements (Stage 6: ADRs, BRDs, FDDs, User Stories) must be formulated and approved to define scope and work packages before the integrated Project Management Plan (Stage 7) and its triple baselines (Scope, Schedule, Cost) can be formally baselined (`PMP-BL-v1.0.0`).
2. **Pillars Full-Coverage Invariant (Invariant 2):** High-level foundational ADRs drafted after the Pillars Exercise must provide 100% full coverage across all identified pillars before moving to detailed requirements.
3. **User Stories ARE Work Packages (Invariant 3):** User Stories derived from FDDs with BDD acceptance criteria constitute the concrete work packages that ground the Scope (5.1/7.A), Schedule (6.1/7.B), Cost (7.1/7.D), and Resource (9.1/7.C) subsidiary plans into the integrated PMP.
4. **Governance Change Impact Matrix (Invariant 4):** Every Adaptation Plan must formally evaluate accepted Stage 16 amendments across all 9 subsidiary management plans using a structured Impact Matrix before selective re-orchestration.
5. **PMP Baseline Versioning & History Archival (Invariant 5):** Every approved PMP receives an immutable SemVer identifier (`PMP-BL-v1.0.0`, `PMP-BL-v1.1.0`). Prior baselines are atomically archived to `docs/project-docs/management-plans/history/{baseline_id}/`.
6. **Baseline Traceability Invariant (Invariant 6):** Every approved PMP, ADR, BRD, FDD, User Story, and Adaptation Plan must record its governing PMP baseline identifier (`pmp_baseline: "PMP-BL-vX.Y.Z"`).
7. **Implementation Authorization Prerequisite (Invariant 7):** No developer may commence implementation work (Stage 9) until the Stage 8 Implementation Readiness Gate formally issues an Execution Authorization Notice reconciling all Stage 6 requirements approvals and the Stage 7 PMP baseline.
8. **Deterministic Rollback Protocol (Invariant 8):** If downstream execution reveals regressions or operational failure (detected via ADR-005 `compare_decision_results()`), atomic rollback restores the prior approved baseline from archive and penalizes the escalation bandit.
9. **Design-Time Revisions Are Patches (Invariant 9):** A baseline revision approved through the design-time loop (§3.1) is a patch increment (`PMP-BL-v1.0.x`); minor increments (`PMP-BL-v1.1.0`) are reserved for Stage 17 adaptations from executed work. The Steering Committee approves a complete revised baseline (a Baseline Revision Package), never an amendment.
