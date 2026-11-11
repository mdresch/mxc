---
artifact_id: implementation-story-queue
version: "1.0.0"
effective: "2026-11-10"
source: Agentic-Parallel-Execution-Policy.md
---

# Implementation story queue — mxc (Tier A integration path)

**Next story** = first row with `queue_status` **queued**. Only **one** row may be **active** at a time.

| # | WBS ID | Epic | Story label | Tier | queue_status | Owner agent | Branch / worktree | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | 1.1.1 | 001 | 1.1 | A | queued | — | — | Gen2 boundary |
| 2 | 1.1.2 | 001 | 1.2 | A | queued | — | — | Guest subsystems |
| 3 | 1.3.1 | 003 | 3.1 | A | queued | — | — | Prod VHDX; RSV-002 |
| 4 | 1.3.2 | 003 | 3.2 | A | queued | — | — | Warm checkpoint |
| 5 | 1.4.1 | 004 | 4.1 | A | queued | — | — | Formulated CPU |
| 6 | 1.4.2 | 004 | 4.2 | A | queued | — | — | Formulated RAM |
| 7 | 1.4.3 | 004 | 4.3 | A | queued | — | — | Resume bench; 4.3 may use direct resume until 1.2.1 |
| 8 | 1.2.1 | 002 | 2.1 | A | queued | — | — | TTFB integration |
| 9 | 1.2.2 | 002 | 2.2 | A | queued | — | — | |
| 10 | 1.2.3 | 002 | 2.3 | A | queued | — | — | HYP-mxc-004 |
| 11 | 1.5.1 | 005 | 5.1 | A | queued | — | — | |
| 12 | 1.5.2 | 005 | 5.2 | A | queued | — | — | |
| 13 | 1.5.3 | 005 | 5.3 | A | queued | — | — | |
| 14 | 1.6.1 | 006 | 6.1 | A | queued | — | — | |
| 15 | 1.6.2 | 006 | 6.2 | A | queued | — | — | |
| 16 | 1.6.3 | 006 | 6.3 | A | queued | — | — | |
| 17 | 1.6.4 | 006 | 6.4 | A | queued | — | — | MS-07 |

## Tier B slots (scaffold — max 3 active)

| slot | WBS focus | integrates | unlock WBS | status | owner |
|---|---|---|---|---|---|
| B1 | — | false | — | idle | — |
| B2 | — | false | — | idle | — |
| B3 | — | false | — | idle | — |

Update this table when an agent claims work; mirror summary in [Project-Status-Register.md](Project-Status-Register.md) §5.
