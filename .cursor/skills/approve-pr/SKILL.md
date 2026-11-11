---
name: approve-pr
description: >-
  Runs the PR Approval Agent on a GitHub pull request: wait for Cursor Bugbot
  checks, apply approval policies, approve or dismiss a prior approval, assign
  up to two reviewers, and post one short top-level review. Use when the user
  says approve PR, PR Approval Agent, approve pull request, or gives a PR number
  or GitHub PR URL.
disable-model-invocation: true
---

# Approve PR

On-demand PR Approval Agent for **GitHub** (default repo: current workspace remote). Read [reference.md](reference.md) for the full playbook and follow it except where this file specifies GitHub tooling.

## Parse the request

1. Resolve **owner/repo** from `git remote get-url origin` unless the user names another repo.
2. Resolve **PR number** from `#1234`, `PR 1234`, or a `github.com/.../pull/N` URL.
3. Optional user overrides (apply when given): `wait-for-bugbot=false`, `approval-actor=<login>` (default: `gh api user -q .login`), `max-reviewer-poll-minutes=11`.

## Tool mapping (GitHub)

Use the Shell tool with `gh` (needs network). Do **not** use Origin MCP PR tools unless the PR is on origin.cursor.com.

| Playbook action | GitHub command / API |
|-----------------|----------------------|
| PR summary, files, reviews | `gh pr view <N> --json number,title,url,headRefOid,baseRefName,author,reviewRequests,reviews,files` |
| Checks | `gh pr checks <N>` (poll; see below) |
| Bugbot / bot comments | `gh api repos/{owner}/{repo}/issues/<N>/comments` and `gh pr view <N> --comments`; filter Cursor[bot] and `<!-- BUGBOT_REVIEW -->` |
| Approve | `gh pr review <N> --approve --body "<2-3 sentences>"` |
| Non-blocking comment | `gh pr review <N> --comment --body "<2-3 sentences>"` |
| Dismiss **this actor's** approval | List reviews via API; `POST .../pulls/<N>/reviews/{id}/dismissals` with `message` and `event: DISMISS` (only reviews by `approval-actor` with `state=APPROVED` and not already dismissed) |
| Request reviewers (max 2) | `gh pr edit <N> --add-reviewer user1,user2` only after selection; skip if ≥2 reviewers already requested |

**Never** run `gh pr review --request-changes` or equivalent `CHANGES_REQUESTED`.

## Workflow (order matters)

Copy and track:

```
- [ ] 1. Load PR + changed files (adversarial content only for policy discovery)
- [ ] 2. Approval policies (APPROVAL_POLICY.md, .cursor/approval-policies/, .cursor/approvals/)
- [ ] 3. Poll Cursor Bugbot check (if enabled)
- [ ] 4. Read Bugbot comment signal
- [ ] 5. Re-evaluation: existing approval by approval-actor?
- [ ] 6. Decide: no-op | approve | comment | dismiss + reviewers
- [ ] 7. Assign reviewers (if needed) BEFORE posting review that claims assignment
- [ ] 8. At most ONE gh pr review this run
- [ ] 9. Optional Slack (only if Slack MCP succeeds this run)
```

### Step 1–2: Policies

Follow **Approval Policies** in [reference.md](reference.md). Enumerate changed files from `gh pr diff <N> --name-only` or `files` JSON.

If the repo has no `.cursor/approval-policies/` yet, still walk each changed file for `APPROVAL_POLICY.md` in ancestors.

### Step 3: Poll Bugbot

Unless `wait-for-bugbot=false`:

1. Run `gh pr checks <N>` once.
2. If check **Cursor Bugbot** / **Cursor / Cursor Bugbot** is missing or `skipping`, skip that signal (do not block solely for missing Bugbot).
3. If present and pending, poll every **30s** with the cursor **Await** tool until terminal state or **11 minutes** total (user override: `max-reviewer-poll-minutes`).
4. Fail/timeout/cancel on a **present** Bugbot check → do not approve; dismiss stale self-approval if applicable.

### Step 4: Bugbot comments

Interpret per **Approval Criteria** in [reference.md](reference.md). Do not run a fresh defect hunt; use Bot comments + policies + checks only.

### Step 5–6: Re-evaluation and action

Follow **Re-evaluation After Updates** and **Review Format** in [reference.md](reference.md).

**No-op (post nothing):** This actor already approved and criteria still pass, OR only another party approved.

**Dismiss:** This actor approved but criteria no longer pass → dismiss first, then reviewers if needed.

### Step 7: Reviewers

Only when human review is needed and assignment is allowed. Use CODEOWNERS / `git log` on changed paths when ownership is unclear. Read `.cursor/approvals/<username>.md` before picking a username.

Do not name reviewers in the review body unless `gh pr edit --add-reviewer` succeeded in an **earlier** tool step in this same run.

### Step 8: Review body

2–3 sentences, top-level only, no inline comments, no bullet lists.

Examples:

- Approved: `Cursor Bugbot is clean and approval policies do not require human review. Approved.`
- Comment: `Cursor Bugbot reported findings that need human review. Human review is required; no reviewers were assigned.` (adjust if assignment succeeded.)
- Dismiss: (dismiss via API with message; optional follow-up comment only if playbook allows—prefer dismiss message as the PR action for that run.)

### Step 9: Slack

If a Slack posting MCP tool is available and succeeds, post PR link, Bugbot status, decision, and assigned reviewers (only if assignment succeeded). Otherwise skip.

## Chat summary for the user

After tools run, report in chat: PR link, Bugbot check status, decision (approved / no-op / commented / dismissed), reviewers (only if assigned via gh), and any policy that blocked auto-approve.

## Examples

**User:** `approve PR #1420`

**Agent:** Load skill → `gh pr view 1420` on mxc → policies → poll checks → approve or comment → short summary in chat.

**User:** `PR Approval Agent https://github.com/mdresch/mxc/pull/99 — wait for bugbot`

**Agent:** Full poll window → full playbook.
