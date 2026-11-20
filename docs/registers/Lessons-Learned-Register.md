---
register: "lessons-learned-register"
governed_by: "ADR-010 (Lessons Learned Crystallization and Register)"
---

# Lessons Learned Register — <project name>

**Lifecycle role:** a light recap held once per epic, after its last user story is implemented and reviewed. It records how the code was created from the stories: traps, defects and review findings. It is not the formal lessons-learned review, and it adds no approval gate and no `LearningStore` record type.

**Maintenance rule:** append-only. Entries are accepted by a human. A recap with nothing new is recorded as a short sign-off entry whose Epic/Phase contains `no-new-lessons` and whose propagation target reads `Tier 1 register sign-off`.

**Propagation tiers.** Tier 1 is this register (always). Tier 2 is the in-repo component skill under `.claude/skills/<component>/SKILL.md`. Tier 3 is the universal rule in the template repository.

## Index

| ID | Title | Epic / Source | Tier Scope | Date |
|---|---|---|---|---|

## Entries

<!--
Copy this block per lesson. Required fields: title in the heading, Epic / Story, The Trap / Problem, The Root Cause, Actionable Invariant / Rule, Tier 2/3 Propagation Target (may read `Tier 1 only`).

### LL-001 — <title>
- **Epic / Story:** Epic <N> / Story <N.M> (PR <link>, commit <hash>)
- **Scope:** <where the lesson applies>
- **Date:** <date>
- **Tier 2/3 Propagation Target:** <skill path, or `Tier 1 only`>
- **The Trap / Problem:** <the real defect or hazard observed>
- **The Root Cause:** <the underlying mechanism>
- **Actionable Invariant / Rule:** <the rule or snippet that prevents recurrence>
-->
