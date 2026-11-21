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
| `LL-001` | Zero-Padded Epic File Matching & AC Parsing Fallback | Epic 01 / Story 1.1 | Tier 2 (`scripts/spec_gate.py`) | 2026-11-21 |
| `LL-002` | Local Store Dir Environment Isolation for Pytest Session | Epic 01 / Story 1.1 | Tier 2 (`tests/conftest.py`) | 2026-11-21 |
| `LL-003` | Ingress Gateway Buffer Holding and Timeout Decoupling | Epic 02 / Story 2.2 | Tier 2 (`ingress-gateway/SKILL.md`) | 2026-11-21 |

## Entries

### LL-001 — Zero-Padded Epic File Matching & AC Parsing Fallback
- **Epic / Story:** Epic 001 / Story 1.1 (commit `9e454974`)
- **Scope:** Specification gatekeeper script (`scripts/spec_gate.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `scripts/spec_gate.py`
- **The Trap / Problem:** `scripts/spec_gate.py` raised `FileNotFoundError` when invoked on Epic 1 (`spec_gate.py 1.1`) because `find_epic_file` globbed only `epic-1-*.md` and `epic-1.md`, failing to match standard 3-digit zero-padded names like `epic-001-type-1-hyperv-generation-2.md`. Additionally, `parse_story_spec` failed to extract criteria when lines lacked `**AC_1:**` bold tags.
- **The Root Cause:** Inflexible file globbing and regex assumptions in `find_epic_file()` and `parse_story_spec()`.
- **Actionable Invariant / Rule:** Support zero-padded globs (`epic-{n:03d}-*.md`, `epic-{n:02d}-*.md`, `epic-{n}-*.md`) and provide a fallback bullet-point extractor for criteria under `**Acceptance Criteria:**`.

### LL-002 — Local Store Dir Environment Isolation for Pytest Session
- **Epic / Story:** Epic 001 / Story 1.1 (commit `9e454974`)
- **Scope:** Governance test runner environment (`tests/conftest.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `tests/conftest.py` / `implement-story`
- **The Trap / Problem:** When `$env:AGENT_LEARNING_LOCAL_STORE_DIR` was set at the user OS level to an external inaccessible path, `conftest.py` failed during session setup with `WinError 5 Access is denied`, halting all pytest tests.
- **The Root Cause:** `conftest.py` captures `os.environ.get("AGENT_LEARNING_LOCAL_STORE_DIR")` at initial import before fixtures run.
- **Actionable Invariant / Rule:** Set `$env:AGENT_LEARNING_LOCAL_STORE_DIR = "data/agent-learning/store"` at process scope before invoking python/pytest runners.

### LL-003 — Ingress Gateway Buffer Holding and Timeout Decoupling
- **Epic / Story:** Epic 002 / Story 2.2 (commit `e9e6e1c1`)
- **Scope:** JIT scale-to-zero reverse proxy gateway (`scripts/lib/ingress_gateway.py`)
- **Date:** 2026-11-21
- **Tier 2/3 Propagation Target:** `.claude/skills/ingress-gateway/SKILL.md`
- **The Trap / Problem:** Direct reverse proxying to a dormant or paused guest socket drops incoming HTTP connections and emits HTTP 502/504 errors, causing webhooks and external callers to abort.
- **The Root Cause:** Off-the-shelf reverse proxies assume downstream socket availability and fail closed on connection reset before hypervisor unpause completes.
- **Actionable Invariant / Rule:** Buffer the incoming socket, asynchronously dispatch `pool-lease` / `resume`, probe guest health on port 8080, and if `wake_timeout_ms` expires, return HTTP 503 with a structured `Retry-After: 2` header, never exposing 502 or 504 to the caller.
