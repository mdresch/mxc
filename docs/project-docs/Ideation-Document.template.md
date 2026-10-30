---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation"
lifecycle_stage: "Stage 1 (Intent) & Stage 3 (Hypothesis)"
governance_policy: "approve-ideation & classify-hypothesis-status"
inputs:
  - "Spark-Capture.md"
  - "Historical telemetry & lessons learned"
process: "Formulate falsifiable hypotheses with empirical evaluation criteria"
outputs:
  - "Ideation-Document.md"
  - "HYP-* hypotheses with status logs"
---

# Ideation Document

> **PMBOK 8 Process:** `Pre-Project / Design Assumption Formulation` (Initiating)  
> **Governance Policy:** `approve-ideation & classify-hypothesis-status` | **Lifecycle Stage:** `Stage 1 (Intent) & Stage 3 (Hypothesis)`  
> **Inputs:** Spark-Capture.md, Historical telemetry & lessons learned  
> **Process:** Formulate falsifiable hypotheses with empirical evaluation criteria  
> **Outputs:** Ideation-Document.md, HYP-* hypotheses with status logs


**Source:** [Spark-Capture.md](Spark-Capture.md)

## Hypotheses

One entry per falsifiable design assumption. Each gets a stable ID (`HYP-<project>-NNN`) and a **dated Update log** — append real test outcomes as they happen, never rewrite the original statement.

### HYP-<project>-001: <statement>
**Status:** Formulated | Testing | Validated | Invalidated | Inconclusive | Blocked
**Updates:**
- <date>: <what was actually tested/found, and what it means for this hypothesis's status>

<If this project has access to `classify-hypothesis-status` (`agent-learning-governance`, shared across projects — see `docs/policy-shapes/`), run it once a hypothesis has a real test outcome to classify, rather than deciding the status line by feel each time.>

## What this is not yet
Objective/Benefit/Capability are separate chain stages. Per this template's own `chain-coverage.md`, none of them currently has strong evidence justifying a separate TaskPolicy — but that doesn't mean skip them in the document itself if this project's own Business Case template expects them. Check real precedent (ADPA, SocialEngage) before assuming they're folded into Hypothesis here too.
