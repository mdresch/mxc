---
name: pr-gate
description: >-
  Runs the SIDPA Bayesian PR gatekeeper (scripts/pr_gate.py) on a GitHub pull
  request: ingests CI status and review/Bugbot text into a DecisionFrame, computes
  robust utility margin, persists a learning episode, and reports pass/fail. Use when
  the user says run pr-gate, pr gate, PR gatekeeper, or gives a PR number after
  fixes and before merge.
disable-model-invocation: true
---

# PR gate (Bayesian gatekeeper)

Mechanical pre-merge gate from **sidpa-template** (`scripts/pr_gate.py`). Complements **approve-pr** (Cursor approval agent): `pr-gate` decides whether evidence supports merge; `approve-pr` posts GitHub approval when Bugbot and policies allow.

## Parse the request

1. Resolve **PR number** from `#N`, `pr-gate N`, or a GitHub PR URL.
2. Optional flags (pass through to the script): `--json`, `--no-persist`, `--merge` (only if the user explicitly asks to merge on pass).

## Run

From repo root (needs `gh` auth and network):

```bash
python scripts/pr_gate.py <N>
```

Or `npm run pr-gate -- <N>`.

Use **--json** when the user wants machine-readable output for chat summary.

## Interpret results

| Exit code | Meaning |
|-----------|---------|
| `0` | Gate **passed** — robust utility margin ≥ +0.05 vs request-revisions |
| `1` | Gate **failed** — revisions required or CI checks failed |

On pass, the script prints approve robust utility and margin. On fail, report the reason string and episode id if persisted under `data/agent-learning/store/`.

**Do not** use `--merge` unless the user explicitly requests merge after a passed gate.

## Typical sequence with approve-pr

1. Fix Bugbot/Q findings on the PR branch.
2. `run pr-gate <N>` — expect fail until critiques are addressed or confidence rises.
3. `approve PR #<N>` — on-demand GitHub approval when Bugbot is clean.

## Agent chat summary

Report: PR link, pass/fail, margin, failed CI checks (if any), critique delta count, episode id. If failed, note this is expected while open review findings remain (e.g. Bugbot issues on PR #3).
