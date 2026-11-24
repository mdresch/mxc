# MXC Autonomous Engineering & Sandbox Protocol
# Harmonized with ECC (Everything Claude Code) Cognitive Guardrails

## Core Engineering Principles
1. **Plan Before Modifying**: Never edit code or invoke commands without first stating a clear hypothesis, risk assessment, and step-by-step implementation plan.
2. **Test-Driven Discipline (TDD)**: Write or update unit/integration tests before writing implementation code. Verify failures before implementing fixes.
3. **Mandatory Sandboxed Execution**: NEVER run untrusted scripts, heavy cargo builds, test suites, or package installations directly on the host machine. Route all execution through the isolated MXC Hyper-V sandbox via MCP tools or PowerShell Direct.
4. **Autonomous Self-Healing**: When a test fails in the sandbox, analyze compiler errors and diagnostics autonomously, adjust code, and re-run without asking the user for trivial permissions.

---

## MXC Hyper-V Sandbox Workflow

When executing commands, testing, or building:
1. **Inspect / Auto-Lease**:
   - MCP tools default to `sandbox_id="auto"`, which automatically checks out a pre-warmed VM from the warm standby pool in `<300ms` or uses the active session.
   - Call `inspect_status` or `session_status` to verify VM health and readiness.
2. **Synchronize Workspace**:
   - Call `sync_workspace_to_guest` to push host workspace state into `C:\workspace` in the guest VHDX via fast VMBus transfer. This automatically creates `.sync_manifest.json` as a baseline tracker.
3. **Defensive Checkpoints & Disposable Mode**:
   - For complex multi-step refactors, call `create_checkpoint(name="pre-refactor")`.
   - For risky installs or speculative one-shot checks, pass `disposable=True` to `execute_command`. This automatically creates an ephemeral checkpoint (or leases a clean pool VM) and rolls back cleanly in a `finally` block, leaving absolute zero state residue.
4. **Isolated Build & Test**:
   - Execute builds and tests inside the VM via `execute_command`.
   - If network access is required (e.g. downloading crates or packages), call `set_network(enabled=True)` (or `mxnet`), execute the build, and immediately restore airgap isolation via `set_network(enabled=False)` (or `mxair`).
5. **Multimodal Visual Inspection**:
   - If testing GUI apps, installers, web dashboards, or Windows console states, call `capture_screenshot` to retrieve a crystal-clear PNG frame from the Hyper-V synthetic video buffer without needing any guest-side agent.
6. **Self-Healing Rollback**:
   - If an experimental refactor fails or corrupts the environment, call `rollback_checkpoint` to restore clean state in ~2 seconds (guest clock is automatically resynchronized).
7. **Lossless Diff Review & Host Application**:
   - Call `export_diff_from_guest` to inspect the exact unified git diff (including additions, modifications, and deletions) tracked against the baseline manifest.
   - Call `apply_guest_changes_to_host(dry_run=True)` to preview changes, then `apply_guest_changes_to_host(dry_run=False)` to losslessly apply verified changes directly back to your host repository.
8. **Release Session**:
   - When finished with a task session, call `session_release()` (or `mxc-pool-release`) to reset the VM back to its clean baseline snapshot and return it to the ready pool.

## Where the project is

Read [`docs/registers/Project-Status-Register.md`](../docs/registers/Project-Status-Register.md) for the active phase, macro stage, and epic. Update §1 of that register at every natural pause. Story step detail belongs in `Story-Execution-Register.md`. Do not re-audit every story to answer which phase, stage, or epic is active. Epic `lifecycle_stage` frontmatter is the authoring-time label, not the project stage.

## Before changing code

- `mxc_sdk::mxc_common` is the cross-platform foundation. Do not move backend execution or enforcement into it, or add new backend implementation dependencies.
- Keep implementation dependencies internal to `mxc-sdk` as Rust modules in the `mxc-sdk` crate, not as separate workspace crates.
- Backend modules generally depend on `mxc_sdk::mxc_common`; avoid cross-dependencies between backend modules. The optional `nanvix_common` module supplies shared MicroVM data/constants rather than backend dispatch.
- `mxc_sdk::mxc_engine` is the single execution engine. Executor binaries and the public SDK facade delegate backend routing to it.
- Keep `wxc`, `lxc`, and `mxc_darwin` thin. Do not add backend-selection matches to the binaries.
- Keep build-time staging in the `mxc-sdk/build/` build modules, not runtime modules.
- Use `#[cfg(target_os = "...")]` and existing Cargo feature gates for platform-specific code.
- Preserve the distinction between run-to-completion, streaming, and state-aware lifecycle APIs.
- Unsupported policy must fail closed. Do not accept a field that the selected backend cannot enforce.

See:

- [`docs/schema.md`](../docs/schema.md)
- [`docs/development/architecture/versioning.md`](../docs/development/architecture/versioning.md)
- [`docs/development/architecture/container-lifecycle.md`](../docs/development/architecture/container-lifecycle.md)
- [`docs/development/build-and-test/ci-validation-infrastructure.md`](../docs/development/build-and-test/ci-validation-infrastructure.md)
- The relevant backend guide under `docs/`

## Build and validation

The Rust toolchain is pinned by `src/rust-toolchain.toml`. Run Rust commands from `src/` or pass `--manifest-path src/Cargo.toml`.

### Builds

```text
build.bat

./build.sh

./build-mac.sh
```

The sidecars declared as `[[bin]]` targets in `src/mxc-sdk/Cargo.toml` are
ordinary Cargo binary targets. Workspace builds compile the targets whose
`required-features` are enabled; do not invoke Cargo recursively from
`mxc-sdk/build.rs`. Build a sidecar directly with
`cargo build -p mxc-sdk --bin <target>`. The `wxc-wslc-daemon` target requires
`--features wslc`. Keep version-resource generation and dependency staging in
the package build script, and keep artifact copying/signing in the repository
build and CI entry points.

### Targeted validation

```text
# From src/ — required before a Rust change is done.
# scripts/validate-rust.sh and scripts/validate-rust.ps1 run these three.
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test -p mxc-sdk --lib
cargo test -p mxc-sdk --lib -- config_parser

# Line coverage (cargo install cargo-llvm-cov). 100 is the floor for a new
# crate or a story module that can meet it. cargo test does not measure this.
cargo llvm-cov --workspace --fail-under-lines 100

# Rerun on save (cargo install cargo-watch)
cargo watch -c -x "test --workspace"

# From sdk/node/
npm test
npm run test:integration

# From sdk/dotnet/ (requires .NET SDK 10+)
dotnet test --solution Microsoft.Mxc.Sdk.slnx
```

Rust story contracts are `#[test]` functions under `src/`, one per acceptance criterion, with a comment naming the story and ADR. They are not Node `tests/contracts/*.test.js` files. Prefer the smallest test command while iterating, then run `cargo test --workspace` so a regression outside that filter fails before the change is done. The build jobs already fail the pull request when `cargo test --locked` exits non-zero. Host-dependent backend suites live under `tests/scripts/`; use the applicable backend guide and `docs/development/build-and-test/ci-validation-infrastructure.md` before running or changing them. The full Rust rules are in [`.github/instructions/rust.instructions.md`](./instructions/rust.instructions.md).

## Schema and policy rules

- Production parsing dispatches through exact closed contracts and their
  version-specific adapters into private `CommonRequestIR` normalization input.
- Preserve optional-field presence through parsing and binding. Apply defaults and semantic validation in the backend.
- New features use their intended permanent JSON location in the exact
  development contract. JSON placement, publication eligibility, and runtime
  experimental authorization are separate. Update the matching closed request
  types, adapt them into `CommonRequestIR` or a phase-specific runtime config,
  and regenerate the registered exact schema and TypeScript artifacts.
- Never edit `schemas/stable/`; released schemas are immutable.
- Never hand-edit generated development schemas or generated TypeScript wire types.
- `schemas/schema-version.json` is the canonical source for compatibility constants.
- In the .NET SDK (`sdk/dotnet/`), every serialized or deserialized wire type
  must be registered as a `[JsonSerializable]` root in `MxcJsonContext`
  (`MxcJsonSerialization.cs`) and routed through the `MxcJson` helpers, so the
  source-generated resolver is used and no path falls back to reflection. When
  you add or change such a type or an options object, add a matching
  serialize/deserialize check to `Microsoft.Mxc.Sdk.AotSmokeTest`; its CI AOT
  publish gate fails on any reflection-dependent path.

See [`docs/development/build-and-test/schema-codegen.md`](../docs/development/build-and-test/schema-codegen.md) for regeneration commands.

## Error and security behavior

- Surface errors explicitly using repository error types and include actionable context.
- Preserve panic containment across `mxc_ffi`; no panic may unwind through the C ABI.
- Preserve exact resource ownership and cleanup contracts, especially for processes, jobs, traces, sessions, and native handles.
- Do not weaken validation or convert failures into success-shaped fallbacks.
- Telemetry is Windows-only, requires explicit user consent, and fails closed. Administrative policy may restrict consent but may never grant it. See [`docs/telemetry.md`](../docs/telemetry.md).

## Documentation

Update documentation in the same change when behavior changes:

- Schema or config fields: `docs/schema.md` and the applicable generated development artifacts.
- Experimental features: `docs/development/guides/authoring-a-new-feature.md`.
- Versioning or promotion: `docs/development/architecture/versioning.md`.
- Backend behavior: the corresponding guide under `docs/`.
- SDK APIs: the affected SDK README and versioned references under `docs/api-reference/{rust,dotnet,node}/v*/`.
- Telemetry: `docs/telemetry.md`.
- CI validation: `docs/development/build-and-test/ci-validation-infrastructure.md`.

Do not duplicate detailed backend behavior here. Keep the canonical explanation in the subsystem documentation.

### Terminology

- In consumer docs and public Rustdoc, replace "state-aware" with "container lifecycle operations" ("manual lifecycle operations" for caller responsibility), "one-shot" with "create-and-run execution", and "exact contract" with "contract".
- Use plain English and explicit type, namespace, field, and format names (e.g. "MXC request JSON"). Avoid "wire type", unqualified "raw JSON", "native request", "closed exclusion", "closes over policy", "operation-neutral", and "pinned logging".
- Preserve code identifiers. Follow the [developer wording guide](../docs/development/glossary.md); define retained jargon in the [consumer glossary](../docs/glossary.md) or developer glossary.

## SDK API consistency

- Publish every SDK operation, type, probe, discovery API, telemetry API, and helper only through a supported versioned (V*) namespace/module/entrypoint.
- Before adding or changing an API or type, compare the corresponding Rust, .NET, and Node references under `docs/api-reference/`. Align names, field meanings, defaults, optional-field presence, input order, and result/ownership semantics across SDKs.
- Use language-idiomatic spelling and construction: Rust snake_case and enums, .NET PascalCase and closed SDK-owned classes, and TypeScript camelCase and discriminated unions. Do not force identical syntax or add convenience abstractions merely to imitate another language.
- Keep authoring requests as typed data. Use consistent policy and backend configuration names; native adapters own wire mapping and the native engine owns semantic validation.
- Keep API-specific controls in the API-specific options type. Creation takes request then options; existing-container execution takes identity, request, then options; .NET cancellation tokens come last.
- Preserve existing behavior and ownership semantics. Do not broaden backend capabilities to manufacture parity.
- Document intentional language/runtime differences explicitly, and update the affected versioned (V*) signature/type references, examples, and tests in the same change.
- Breaking changes to a published SDK API require a new versioned (V*) API surface and matching signature/type references. Preserve the published version's references.

## Issues and pull requests

Use the repository templates as the source of truth:

- Issues: `.github/ISSUE_TEMPLATE/`
- Pull requests: `.github/PULL_REQUEST_TEMPLATE.md`

When creating issues through an API, explicitly set the issue type and these exact labels:

| Category | Type | Labels |
|----------|------|--------|
| Bug report | `Bug` | `Issue-Bug`, `Needs-Triage` |
| Feature request | `Feature` | `Issue-Feature`, `Needs-Triage` |
| Documentation issue | `Task` | `Issue-Docs`, `Needs-Triage` |
| Task | `Task` | `Issue-Task`, `Needs-Triage` |

Do not fabricate missing required issue fields. For security issues or BSODs, do not attach dumps, logs, or traces to a public GitHub issue; direct sensitive material to `secure@microsoft.com` and reference the issue.
