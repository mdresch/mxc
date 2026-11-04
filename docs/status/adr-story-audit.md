# ADR and story audit

Judged against the SIDPA `implement-story` skill, not against the Hyper-V implementation plan's own completion marks.

| Item | Value |
|---|---|
| Skill | [`.claude/skills/implement-story/SKILL.md`](https://github.com/mdresch/sidpa-template/blob/5fb4f20bf1979251affa3528a96db49a0cb6968e/.claude/skills/implement-story/SKILL.md) in `mdresch/sidpa-template` @ `5fb4f20` (4 Nov 2026, 09:14 Europe/Amsterdam) |
| Skill in this repo | Absent. `.gitignore` ignores `.claude/`. No `SKILL.md` is tracked on `main` or `feat/hyperv-v2-rebased`. |
| Code and documents audited | `origin/feat/hyperv-v2-rebased` @ `06a630d4` (30 Oct 2026, 15:44 Europe/Amsterdam) |
| `main` | No ADR, BRD, FDD, user story, or Hyper-V backend. Tip `3d0d9dd0` (15 Oct 2026, 16:17 Europe/Amsterdam). |

## Definition of done used

From the skill's own "Definition of done" and the mandatory loop (steps 0–9). A story is implemented only when all of these are true:

1. `validate-intent-foundation` has cleared the already-accepted ADR/BRD/FDD/story chain, and that sign-off is on the story's Status line. Document approval (`approve-adr`, `approve-brd`, `approve-fdd`, `approve-user-stories`) is a different gate.
2. Step 0: a fresh worktree on `feat/story-<X.Y>` from the confirmed base branch. An existing story branch is resumed with `heal-contract-failure`, not re-implemented.
3. Step 1: story Status is Ready (never Blocked); ADR, BRD, and FDD are read; named data paths are tracked in git.
4. Step 2: intent, file scope, contract paraphrase, and explicit out-of-scope are stated.
5. Step 3: one contract test per acceptance criterion, header comment naming the story and ADR, observed failing (RED) before implementation. Rust (`cargo test`) and C# are unevidenced in the methodology; the first MXC story must confirm the runner, fixture path, and worktree provisioning, then correct this project's copy of the skill. The template CLI looks for `tests/contracts/*.test.js` and `node --test`. That path is a template default, not this repo's convention.
6. Step 4: a component `SKILL.md` naming governing ADRs, contract files, and constraints.
7. Step 5: minimal implementation that turns the contract green.
8. Step 6: that contract, then the whole accumulated contract suite in every language the project uses.
9. Step 7: `npm run story:done <STORY-ID>` (`scripts/complete-story.mjs`), which runs the contract, stamps `docs/registers/Story-Execution-Register.md`, and makes one commit. The skill also requires an `implementation-log.md` entry.
10. Step 8: a pull request. Direct push to the default branch does not count.
11. Step 9, last story of the epic only: breakout recap recorded in `Lessons-Learned-Register.md` (`LL-###` or a no-new-lessons sign-off) and `Continuous-Improvement-Register.md` (`IMP-###` or a no-new-ideas sign-off).
12. `docs/registers/Project-Status-Register.md` §1 matches the real stage. Do not read stage from a document's `lifecycle_stage` frontmatter: BRD, FDD, epic, and PMP in this chain all stamp `Stage 7` for different meanings.

The Story Execution Register on the Hyper-V branch is the template and is empty. No story id has a row. No `tests/contracts/` tree, no root `package.json` `story:done` script, no `implementation-log.md`, no `Project-Status-Register.md`, no lessons or continuous-improvement registers. Under this definition every story below is **not started**, including stories that already have prototype code.

## Governance sequence (from `sidpa-template`)

Authoring order, from `.claude/skills/pmbok-planning/SKILL.md`, `.github/instructions/sidpa-governance-qa.instructions.md`, and `docs/chain-coverage.md`. Each arrow is a cite-the-previous-document rule. Each boxed gate is a `DecisionAuthority.FULL` policy with `requires_human_approval: true`.

1. Spark Capture → Ideation → Business Case and Benefits Statement → Project Charter (`approve-ideation`, `approve-business-case`, `approve-charter`).
2. Pillars exercise: 4–6 pillars. Every pillar has at least one ADR.
3. ADR (`approve-adr`) → BRD (`approve-brd`) → FDD (`approve-fdd`) → user stories with acceptance criteria (`approve-user-stories`). Each cites the one before it and does not restate it.
4. Subsidiary management plans and the integrated PMP (`approve-pmp`), baseline id `PMP-BL-vX.Y.Z` copied into downstream frontmatter. Schedule and cost wait for real story data.
5. **Pipeline entry:** `validate-intent-foundation`. Approval of the documents does not authorize `implement-story`.
6. **Per story:** `implement-story` steps 0–8, then step 9 on the epic's last story. A broken or review-found contract is `heal-contract-failure` (re-walk intent → make the contract RED → update the component skill → then change code), capped at three walks.
7. After delivery: audit register (`approve-audit-record`), lessons, governance change (`classify-diff-type` then `escalate-diff-response`), adaptation plan (`approve-adaptation-plan`), intent refinement (`approve-intent-refinement`).

MXC's numbered packs ADR/BRD/FDD/epic 001–006 are past step 3 (gates dated 30 Oct 2026, human acceptance recorded under the template policy ids). They have not passed step 5 or step 6. The audit register is still the empty template (`<project>`, no `AUDIT-001`).

## ADR status

"Document status" is the lifecycle ADR under `docs/07-architecture/` plus the suite record in `docs/hyperv/architecture/ADR.md`. "Code" is what `06a630d4` actually contains. "Skill" is the definition of done above.

| ADR | Document | Linked BRD / FDD / stories | Code on `06a630d4` | Skill |
|---|---|---|---|---|
| ADR-001 Type-1 Hyper-V Generation 2 | Accepted, `approve-adr` 30 Oct 2026. Pillar TP-01. | BRD-001, FDD-001, Epic 001 stories 1.1, 1.2. Suite BDR-03. | Partial. `src/mxc-sdk/src/backends/hyperv/` creates Generation 2 VMs (`DEFAULT_GENERATION = 2` in `lifecycle/pool.rs` and `lifecycle/state_aware.rs`). No contract that Hyper-V reports Generation 2, and no recorded container-namespace rejection for story 1.2 (WMI, COM+, service, Group Policy). | Not started |
| ADR-002 Connection-buffering ingress | Accepted. Pillar TP-02. | BRD-002, FDD-002, stories 2.1, 2.2, 2.3. Suite US-01. | Partial. `scripts/hyperv/dev_harness/jit_ingress_gateway.py` holds the request, calls pool lease, probes `:8080/health`, and path-routes `/api/v1/adpa` and `/api/v1/sidpa`. No contract tests. Wake failure returns HTTP 503. Story 2.3's listen-port route (`:8091`) is in the image registry, not in `_route_request`. The FDD names TLS `:443` (YARP/Envoy); the file is a plain HTTP harness. Second-factor product is still unnamed in the ADR, so sign-in cannot be scripted. | Not started |
| ADR-003 Production base image | Accepted. Pillar TP-03. | BRD-003, FDD-003, stories 3.1, 3.2. Suite US-04, REQ-BDR-04. | Partial scripts, image absent. `scripts/hyperv/audit_production_image.ps1` and `bake_production_adpa_image.ps1` exist and hash a VHDX with SHA-256. `GOLDEN_IMAGE_REGISTRY.md` and `golden_image_registry.json` list `winserv2025-prod-adpa.vhdx` nowhere. The ADPA image is `img-adpa-poc-v1`, path `winserv2025-adpa-poc.vhdx`, status `poc_planned`. ADR-005 itself says `BEN-08` waits on that bake. | Not started |
| ADR-004 Paused RAM standby | Accepted. Pillar TP-04. | BRD-004, FDD-004, stories 4.1, 4.2, 4.3. Suite US-03. | Partial. `Suspend-VM` / `Resume-VM` in `common/cmdlets.rs`; pool lease and release call them. Unit tests cover state transitions, not a measured ≤300 ms resume, 0.0% idle CPU, or a 1.0–1.2 GB trimmed footprint. Pool members start at 6 GB (`DEFAULT_MEMORY_STARTUP_BYTES`). | Not started |
| ADR-005 Transient differencing disk and egress whitelist | Accepted. Pillar TP-05. | BRD-005, FDD-005, stories 5.1, 5.2, 5.3. Suite US-02, REQ-BDR-03. | Partial, and the ADR's own hypotheses stay `Formulated`. Differencing disks are created (`new_differencing_disk`). Release restores snapshot `pool-clean-baseline` and suspends; it does not delete the `.avhdx` (AC-02.1) and does not check the parent SHA-256 (AC-02.2). `configure_port_acls.ps1` exists and is invoked from `mxc_mcp_server.py`, not from the Rust lease path. No discard-and-reproduce run is recorded. Whole-guest reproduction waits on the production image. WORM RAM disks are the named future horizon (Phase 4). | Not started |
| ADR-006 Watermark pool, replenish, wake hygiene | Accepted. Pillar TP-06. | BRD-006, FDD-006, stories 6.1–6.4. Suite US-05, REQ-BDR-05. | Partial. `lifecycle/pool.rs` has per-pool state, lease, background replenish, and release, with unit tests. Member states are `Ready` / `Leased` / `Recycling`. The FDD states are `ColdProvisioned` / `StandbyPaused` / `ActiveRunning`. Gateway surge uses 10 rps. The ADR still records both 5 rps and 10 rps, and both 180 s and 300 s cooldowns, and leaves `BEN-09` open. Entropy reseed, clock step, and DB-pool flush live in `mock_adpa_service.py`, not the control plane. `pool-warm` exists on the `wxc` CLI (manual pre-warm, AC-05.3). No forecast model. | Not started |
| ADR-007 Hardware PRNG and DB pool purge | No file. `docs/hyperv/README.md` says the text lives inside suite ADR-006 and was never given its own heading. `IMPLEMENTATION_PLAN.md` marks it 100% complete. | No BRD-007, FDD-007, or epic. The behavior is story 6.3 / suite AC-02.4. | Same evidence as story 6.3: guest mock service, not a control-plane contract. | Not started |
| ADR-008 Authentication-gated, identity-bound leasing | Proposed in `docs/hyperv/architecture/ADR.md` only (23 Oct 2026 note in the Hyper-V README). No `docs/07-architecture/ADR-008-*.md`, no gate JSON. The tip commit message names ADR-008. | No BRD, FDD, or story. The ADR says US-01–US-05 do not cover it. | No `auth_gated` or `leasing_mode` in Rust or the gateway. | Not started. Do not enter `implement-story` until an ADR → BRD → FDD → story chain exists and `validate-intent-foundation` clears it. Identity-bound leasing changes ADR-005's unconditional rollback, so it needs its own decision, not a silent extension of story 2.x. |

Future horizons inside ADR-001 through ADR-006 (micro-VM under 256 MB, WebSocket/SSE suspension, SBOM/Cosign, NVMe hibernation tier, WORM scratch disks, predictive pre-warm, session hand-back) are `Formulated` hypotheses. The skill says an ADR whose decision is "a convention for future work" correctly produces zero code-shaped stories. They are not missing stories.

Suite `USER_STORIES.md` US-01 through US-05 are the same acceptance criteria the epics cite (`AC-01.1` … `AC-05.4`). They are not a second backlog. AC-05.3 (schedule or `pool-warm` pre-warm) has no epic story of its own; the closest rows are 6.1 and 6.2.

BDR/FDD requirements in the numbered packs all have a story. REQ-BDR-01 maps to 2.1 and 4.3, REQ-BDR-02 to 6.4 (cooldown still double-valued), REQ-BDR-03 to 5.2, REQ-BDR-04 to 3.1, REQ-BDR-05 to 6.1 and 6.2.

## Stories still to implement

Suggested order follows the ADR dependency notes. Each row is still "not started" under the skill. "Code already present" means a later `implement-story` run must re-walk that code with `heal-contract-failure` if a `feat/story-*` branch is cut on top of it: show the new contract RED before trusting the existing code.

Install the skill into this repo's `.claude/skills/` and instantiate `Project-Status-Register.md` before story 1.1, as the skill requires. Confirm the base branch first: story worktrees belong on `feat/hyperv-v2-rebased`, because `main` has none of this backend. Confirm contract location on story 1.1 (`cargo test` in the Hyper-V crate, plus any PowerShell/Python contract the AC actually needs). The template's `tests/contracts/*.test.js` runner is unevidenced for this repo.

| Order | Story | Depends on | Why this position |
|---|---|---|---|
| 1 | 1.1 Generation 2 isolation boundary | Pipeline entry gate | Every later guest is a Generation 2 VM. Code already passes `2` into `New-VM`. The missing piece is the contract and the recorded rejection of a shared-kernel container (`BRU-001-02`). |
| 2 | 1.2 Windows subsystems on the guest | 1.1 | WMI, COM+, a Windows service, and Group Policy must succeed in the guest and fail or be unsupported in a container namespace (`BEN-05`). No such record exists. |
| 3 | 4.3 Sub-300 ms resume | 1.1 | ADR-002's 800 ms first byte includes this 300 ms platform ceiling. `Resume-VM` exists; the timing contract does not. |
| 4 | 4.1 Zero idle CPU, then 4.2 trimmed footprint | 4.3 | Both are host measurements (0.0% CPU across standby guests; about 1.0–1.2 GB after trim). Pool provision currently requests 6 GB. |
| 5 | 3.1 Clean production VHDX, then 3.2 warm `baseline-hot-ready` checkpoint | 1.1 | Audit and bake scripts exist. The catalog has no `winserv2025-prod-adpa.vhdx`. ADR-005 blocks parent-hash and whole-guest reproduction on this image. Epic 003's last story (3.2) owes the step 9 recap. |
| 6 | 5.1 Ephemeral session disk | 3.2, pool release | AC-02.1 deletes the `.avhdx` after session end or 300 s idle. Release today restores `pool-clean-baseline` and suspends. Parent SHA-256 (AC-02.2) is part of this story. |
| 7 | 5.2 Egress whitelist | 5.1 | `configure_port_acls.ps1` encodes the port list. It is not applied on lease, and no contract drops public egress while allowing SQL `:1433`, PostgreSQL `:5432`, blob `:443`, DNS `:53`, Kerberos `:88`. |
| 8 | 5.3 Discard and reproduce | 3.2, 5.1 | ADR-005 says no discard-and-reproduce run has been captured, and the whole-guest path stays open while the production image is unfinished. |
| 9 | 6.1 Buffer replenishment, 6.4 scale-down | 4.x, 5.1 | Replenish-on-lease has unit tests. Resolve the 180 s vs 300 s cooldown in the ADR before writing the 6.4 contract, so one figure is the criterion. |
| 10 | 6.2 Surge expansion | 6.1 | Gateway implements 10 rps. ADR-006 also cites 5 rps. Pick one figure, then encode it. |
| 11 | 6.3 Wake hygiene | 6.1, 4.3 | PRNG reseed, clock sync, and DB-pool clear run inside `mock_adpa_service.py` before `/health` returns 200. That is the AC-02.4 behavior ADR-006 owns. Last story of epic 006, so step 9 applies. |
| 12 | 2.1 Cold-wake TTFB, 2.2 no wake-caused 502/504 | 4.3, 6.1 | Gateway prototype exists. Contracts must hold the paused-guest POST to ≤800 ms (AC-01.1), warm proxy overhead ≤5 ms (AC-01.2), and show wake latency does not produce 502/504 (AC-01.3). |
| 13 | 2.3 Dual routing | 2.1 | Path routing to `prod-adpa` / `prod-sidpa` is in the gateway. Listen-port `:8091` → catalogued ADPA image is not. Last story of epic 002, so step 9 applies. |

AC-05.3 (scheduled or manual pre-warm) is in suite US-05 and has no epic story. `wxc --hyperv-op pool-warm` is the manual half. Add a story under epic 006, or record in the FDD that manual `pool-warm` is the whole current target and schedule-based pre-warm stays the ADR-006 horizon, before treating US-05 as closed.

ADR-008 waits until its own BRD, FDD, and stories exist. It depends on ADR-002's gateway and must say explicitly whether a route opts out of ADR-005 rollback.

## Doc and status mismatches

1. `docs/hyperv/architecture/IMPLEMENTATION_PLAN.md` marks ADR-001, ADR-002, ADR-003, ADR-004, ADR-006, ADR-007, and US-01 through US-05 as 100% complete, and ADR-005 as active. The Story Execution Register says no story has run. Story status lines still say "Ready for review — not yet run through `implement-story`". Those are different claims. The skill forbids treating scattered code as a completed step.
2. The same plan's Phase 1 table marks ADR-005 differencing disks complete, and the summary table marks ADR-005 active. ADR-005's own text leaves `HYP-mxc-013`, `HYP-mxc-022`, `BEN-07`, and `BEN-12` as `Formulated`.
3. ADR-003 is marked 100% complete in the plan. The golden-image registry status for the ADPA image is `poc_planned`, and the filename in the ADR (`winserv2025-prod-adpa.vhdx`) is not the registry filename (`winserv2025-adpa-poc.vhdx`).
4. Snapshot name: ADR/FDD/bake scripts say `baseline-hot-ready`. `pool.rs` restores `pool-clean-baseline`. The registry JSON carries both fields.
5. Pool state names in the FDD (`ColdProvisioned`, `StandbyPaused`, `ActiveRunning`) are not the enum in `pool.rs` (`Ready`, `Leased`, `Recycling`).
6. ADR-007 is cited as a completed ADR and has no document, no gate, and no story id.
7. ADR-008 is Proposed in the suite ADR file. The 30 Oct 2026 commit message presents it as part of the deliverable. There is no lifecycle pack and no approval gate.
8. `LESSONS_LEARNED.md` and `SCOPE_DRIFT_AND_UPSTREAM_MAINTENANCE.md` cite git baseline `4e1de794` / `ecf62a48`. The branch tip is `06a630d4`. Those files are a retrospective, not the skill's `Lessons-Learned-Register.md`.
9. Every lifecycle ADR, BRD, FDD, and epic stamps `lifecycle_stage: Stage 7` for a different process (architecture, business, solution, story). The skill's Project Status Register exists to stop readers treating that label as the project stage. The register file is missing, so the overload is unrecorded.
10. `validate-intent-foundation` is described in `docs/sequence-and-lessons.md` and the epic "Before running implement-story" notes, and no story Status line records a recommendation or a human sign-off.
11. `docs/registers/Audit-Register.md` is still the template (`Audit Register — <project>`, empty finding table).
12. The Hyper-V README dates ADR-008 as Proposed 23 Oct 2026. The suite ADR has no separate date line beyond "October 2026".
