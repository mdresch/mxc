---
description: Universal Quality Assurance and Process Directives for SIDPA Governance Artifacts
applyTo: 'docs/**'
---

# SIDPA Governance Artifact Quality Assurance Directives

These directives govern AI agent behavior when drafting, reviewing, or revising project governance documents in SIDPA repositories (PMBOK 8 / BABOK).

---

## 1. Universal Artifact Authoring Directives

1. **Negative Scope Boundary ("What this is not yet"):**
   - Every early-stage document (`Spark-Capture.md`, `Ideation-Document.md`, `Project-Charter.md`) MUST explicitly contain a section declaring what is intentionally excluded and deferred to downstream stages.
   - **Anti-Stage Collapsing Invariant:** NEVER jump ahead to database schemas, API routes, or code-shaped details in an Intent or Charter document.

2. **Problem-Before-Solution Discipline:**
   - Articulate the mechanical friction, operational breakdown, and organizational failure mode in concrete, unsanitized terms before introducing the technical capability or solution.

3. **Standardized PMBOK 8 / IPO Frontmatter:**
   - Every governance document MUST begin with standardized YAML frontmatter:
     ```yaml
     ---
     pmbok_edition: "PMBOK 8"
     pmbok_process_group: "<Initiating | Planning | Executing | Monitoring & Controlling | Closing>"
     pmbok_process: "<Process Number & Name>"
     lifecycle_stage: "<Stage Number & Name>"
     governance_policy: "<assigned-policy-name>"
     inputs:
       - "<input 1>"
     process: "<brief description of process>"
     outputs:
       - "<output 1>"
     ---
     ```

4. **Non-Duplication Principle:**
   - Never re-derive or restate the reasoning of an upstream document. Cite it directly:
     - `Ideation-Document.md` cites `Spark-Capture.md`
     - `Business-Case.md` cites `Ideation-Document.md`
     - `Benefits-Statement.md` cites `Business-Case.md` (and is an input to Charter)
     - `Project-Charter.md` cites `Benefits-Statement.md`
     - `PILLARS-EXERCISE.md` cites `Project-Charter.md`
     - `ADR-*.md` cites `PILLARS-EXERCISE.md`
     - `BRD-*.md` cites `ADR-*.md`
     - `FDD-*.md` cites `BRD-*.md`
     - `User Stories` cite `FDD-*.md`

5. **Human Adjudication Gate Invariant:**
   - Always default `requires_human_approval: true` for all governance policies. Never fabricate approval evidence or mark a gate as accepted without explicit human confirmation.

6. **Zero Template Clutter Invariant:**
   - When instantiating active `.md` documents, remove redundant `.template.md` files from project directories to maintain a clean workspace.

---

## 2. The Pillars & Work Package Derivation Sequence

Follow the strict post-Charter architecture and planning sequence:

```
[Spark Capture] -> [Ideation] -> [Business Case & Benefits] -> [Project Charter]
                                                                        ↓
                                                               [Pillars Exercise]
                                                                        ↓
                                                            [High-Level ADRs (100% Coverage)]
                                                                        ↓
                                                                      [BRD]
                                                                        ↓
                                                                      [FDD]
                                                                        ↓
                                                           [User Stories (Work Packages)]
                                                                        ↓
                                                       [PMP Subsidiary Plans (5.1, 6.1, 7.1, 9.1) & PMP]
```

* **The Pillars Exercise:** Decompose the approved Project Charter into 4–6 mutually exclusive, collectively exhaustive architectural and capability pillars.
* **100% ADR Pillar Coverage:** Every identified pillar must have at least one governing high-level ADR. No pillar may be left floating without architectural ownership.
* **User Stories ARE Work Packages:** Do not draft Schedule (6.1) or Cost (7.1) management plans with speculative numbers immediately after the Charter. The User Stories derived from FDDs provide the concrete story points, velocity, and task activities required to ground the subsidiary plans and the integrated Project Management Plan (PMP).

