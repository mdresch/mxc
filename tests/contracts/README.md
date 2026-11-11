# Story contracts — mxc (polyglot)

Contracts encode **approved user-story acceptance criteria** and must fail (RED) before implementation.

## Layout (v1)

```
tests/contracts/           # Node integration / gateway (when added)
  epic-002/
    story-2.1.test.js      # Header: Story 2.1, WBS 1.2.1, ADR-002
src/**/tests/              # Rust: #[test] in crate or mod tests (primary for wxc)
tests/sidpa/               # Governance tooling (pytest) — not product story contracts
```

## Story ID in contract headers

Use **both** for agent search (`complete-story.mjs`, humans):

```text
// Story 1.1 — Gen2 boundary (ADR-001) | WBS 1.1.1
```

## Step 6 validation (implement-story)

Run **all** applicable suites for the story:

1. `npm run test` — all `tests/contracts/**/*.test.js` (if any exist).
2. `cargo test` — crates listed in the component `.claude/skills/<component>/SKILL.md` for Rust deliverables.
3. Integration harnesses (sandbox) — only Tier A; document command in story Intent.

## Fixtures

Commit under `tests/fixtures/<epic>/` or `src/.../fixtures/`. Never rely on gitignored repo-root data (agent-learning lesson).
