"""Generate lifecycle BRD, FDD, and epic files for ADR-001..006."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BRD_DIR = REPO / "docs" / "project-docs" / "Business-Requirements"
FDD_DIR = REPO / "docs" / "project-docs" / "Functional-Design"
STORY_DIR = REPO / "docs" / "user-stories"
BASELINE = "PMP-BL-v1.0.0"
ADR_ACCEPT = (
    "`approve-adr` accepted `approve_adr` on 2026-10-30 "
    "(policy `0063adbf-5659-426d-950b-b2eaab87fb34`)"
)

PACKS = [
    {
        "n": "001",
        "slug": "type-1-hyperv-generation-2",
        "title": "Type-1 Hyper-V Generation 2 instead of a container namespace",
        "bdr": "BDR-03",
        "suite_us": None,
        "brd_need": (
            "ADPA and SIDPA process confidential records. The business requires a hardware boundary "
            "that does not share the host kernel with neighbor workloads. The always-on server and "
            "the shared-kernel container are rejected for this bar."
        ),
        "brus": [
            ("BRU-001-01", "The production workload runs only in a Type-1 Hyper-V Generation 2 guest.", "ADR-001 §4.1"),
            ("BRU-001-02", "A shared-kernel container does not satisfy the isolation bar for these records.", "ADR-001 §4.2"),
            ("BRU-001-03", "WMI, COM+, a Windows service, and Group Policy must succeed inside that guest.", "ADR-001 §4.3"),
            ("BRU-001-04", "An idle guest is Paused, not left Running; it does not accept a new session while Paused.", "ADR-001 §4.4"),
        ],
        "metrics": [
            ("Generation 2 guest in use for ADPA/SIDPA pools", "Formulated (`HYP-mxc-006`); not re-measured for lifecycle docs"),
            ("Named Windows subsystems succeed in guest vs container", "Formulated (`HYP-mxc-009`, `BEN-05`); side-by-side check not run"),
            ("Paused guest rejects direct service connection", "Formulated (`HYP-mxc-021`, `BEN-11`); exposure comparison not run"),
        ],
        "oos": [
            "Ingress buffering, TTFB ceilings, and routing (`ADR-002`).",
            "Paused RAM, CPU, GPU, and disk footprint readings (`ADR-004`).",
            "Production image contents and bake (`ADR-003`).",
        ],
        "fdd_design": """### Hyper-V partition model
* **Control plane:** `wxc-exec --features hyperv` (Rust Hyper-V backend under `src/mxc-sdk/src/backends/hyperv/`).
* **Guest class:** Generation 2 VM with its own kernel; not a container namespace on the host.
* **Idle posture:** Guest reaches `Paused` through the lifecycle controller; session acceptance while `Paused` is forbidden (resume is owned by ingress + pool).

### Verification hooks
| Check | Contract |
|---|---|
| Partition generation | Hyper-V reports Generation 2 for pool members |
| Subsystem probe | WMI query, COM+ activation, Windows service start, Group Policy refresh succeed in guest |
| Paused socket | Direct TCP to guest `:8080` fails while `Paused`; succeeds only after lease/resume |
""",
        "fdd_errors": [
            ("Container runtime requested for confidential pool", "Reject provisioning; cite `ADR-001` and `BDR-03`"),
            ("Guest left Running with no sessions", "Violates sterility posture; pool manager must suspend per `ADR-004`"),
        ],
        "stories": [
            (
                "1.1 — Generation 2 isolation boundary",
                "Platform Engineer",
                "provision ADPA and SIDPA on Generation 2 Hyper-V guests",
                "confidential workloads never share the host kernel",
                [
                    "Given a new pool member, when provisioned, then Hyper-V reports Generation 2 and a guest kernel distinct from the host.",
                    "Given a shared-kernel container proposal for the same records, when evaluated against this epic, then it is rejected with reference to `BRU-001-02`.",
                ],
            ),
            (
                "1.2 — Windows subsystems on the guest",
                "Software Release Engineer",
                "run WMI, COM+, a Windows service, and Group Policy inside the guest",
                "legacy Windows automation required by ADPA/SIDPA remains in scope",
                [
                    "Given the Generation 2 guest from Story 1.1, when each named subsystem is invoked, then the call succeeds in the guest.",
                    "Given the same calls attempted in a container namespace baseline, then they fail or are unsupported, and the difference is recorded for `BEN-05`.",
                ],
            ),
        ],
    },
    {
        "n": "002",
        "slug": "connection-buffering-ingress-gateway",
        "title": "Connection-buffering ingress gateway",
        "bdr": "BDR-02",
        "req": "REQ-BDR-01",
        "suite_us": "US-01",
        "brd_need": (
            "Callers send ordinary HTTPS while guests are Paused. The business requires sub-second response "
            "without cold-boot waits and without wake-caused gateway failures."
        ),
        "brus": [
            ("BRU-002-01", "The gateway holds the client request while the target guest is Paused.", "ADR-002 §4.2"),
            ("BRU-002-02", "First byte from a Paused guest arrives within 800 ms; warm traffic is measured separately.", "ADR-002 §4.3"),
            ("BRU-002-03", "Path and listen-port routing both apply; the check records which rule fired.", "ADR-002 §4.5"),
            ("BRU-002-04", "Wake does not produce HTTP 502 or 504; HTTP 503 after wake timeout is a different case.", "ADR-002 §4.4"),
            ("BRU-002-05", "Username, password, and a second factor use the same wake; typing time is outside the ceilings.", "ADR-002 §4.6"),
        ],
        "metrics": [
            ("Cold TTFB from Paused guest", "Formulated (`HYP-mxc-003`); ≤ 800 ms ceiling in `AC-01.1`"),
            ("Resume-VM duration included in TTFB path", "Owned by `ADR-004`; ≤ 300 ms in `AC-03.3`"),
            ("Second-factor product for sign-in scripts", "Unnamed; `BEN-06` cannot be scripted yet"),
        ],
        "oos": [
            "300 ms `Resume-VM` measurement (`ADR-004`).",
            "Kerberos whitelist details (`ADR-005`).",
            "Clock step before sign-in (`ADR-006`).",
        ],
        "fdd_design": """### JIT ingress gateway (`scripts/hyperv/dev_harness/jit_ingress_gateway.py`)
* Terminates TLS, matches `/api/v1/adpa/*` → `prod-adpa` and `/api/v1/sidpa/*` → `prod-sidpa`.
* Catalogued listen ports `:8090`, `:8091`, `:8092` select the bound image; guest service port `:8080`.
* On dormant target: hold buffer, call `pool_lease` / `resume`, poll `:8080/health`, flush request.
* `wake_timeout_ms` default 3000 → HTTP 503 with `Retry-After` (not 502/504 from wake).

### Route schema (suite `FDD.md` §2.1)
```json
{
  "match_path": "/api/v1/adpa/{**catch-all}",
  "target_pool": "prod-adpa",
  "guest_port": 8080,
  "wake_timeout_ms": 3000,
  "health_check_path": "/health"
}
```
""",
        "fdd_errors": [
            ("Resume exceeds wake_timeout_ms", "HTTP 503 with Retry-After; do not drop TCP (`AC-01.3`)"),
            ("Guest already Running", "Forward immediately; warm path ≤ 15–25 ms proxy overhead (`AC-01.2`)"),
        ],
        "stories": [
            (
                "2.1 — Cold wake TTFB",
                "Enterprise Automation Operator",
                "POST to ADPA/SIDPA while the guest is Paused",
                "I receive the first byte without a cold boot",
                [
                    "Given target VM Paused, when POST arrives, then gateway holds, wakes, and first byte ≤ 800 ms (`AC-01.1`).",
                    "Given VM Running, when subsequent requests arrive, then proxy overhead ≤ 5 ms plus app time (`AC-01.2`).",
                ],
            ),
            (
                "2.2 — No wake-caused 502/504",
                "Enterprise Automation Operator",
                "send HTTPS during wake",
                "I do not see gateway 502 or 504 caused by wake latency",
                [
                    "Given normal conditions, when the guest wakes, then response is not HTTP 502 or 504 because of wake (`AC-01.3`, `BEN-03`).",
                    "Given wake exceeds wake_timeout_ms, when timer fires, then HTTP 503 with Retry-After is returned.",
                ],
            ),
            (
                "2.3 — Dual routing rules",
                "DevOps Engineer",
                "route by path and by catalogued listen port",
                "the request reaches the owning image",
                [
                    "Given path `/api/v1/adpa`, when leased, then pool is `prod-adpa` and the check records path routing (`HYP-mxc-004`).",
                    "Given listen port `:8091`, when accepted, then image is the catalogued ADPA PoC image and the check records port routing.",
                ],
            ),
        ],
    },
    {
        "n": "003",
        "slug": "production-base-image",
        "title": "Production base image separate from the developer image",
        "bdr": "BDR-04 (packaging)",
        "req": "REQ-BDR-04",
        "suite_us": "US-04",
        "brd_need": (
            "Production must not run from the developer golden image. Attack surface and bake hygiene require a "
            "separate VHDX with no toolchain and a warm checkpoint."
        ),
        "brus": [
            ("BRU-003-01", "Production pool parent is `winserv2025-prod-adpa.vhdx`, not `winserv2025-mxc-dev.vhdx`.", "ADR-003 §4.1"),
            ("BRU-003-02", "Inventory finds no Scoop, cargo, git, compiler, uv, or source repositories on the production VHDX.", "ADR-003 §4.3"),
            ("BRU-003-03", "Checkpoint `baseline-hot-ready` is taken after smoke on `localhost:8080/health`.", "ADR-003 §4.4"),
            ("BRU-003-04", "Image signing and vulnerability scan stay future until `HYP-mxc-017` is implemented.", "ADR-003 §4.6"),
        ],
        "metrics": [
            ("Production VHDX in catalog", "Not present yet; `BEN-08` unrealized"),
            ("Clean inventory (`AC-04.1`)", "Blocked on finished bake"),
            ("Warm checkpoint after smoke (`AC-04.2`)", "Blocked on finished bake"),
        ],
        "oos": [
            "Session `.avhdx` discard (`ADR-005`).",
            "Paused RAM footprint (`ADR-004`).",
            "Cosign/SBOM horizon (`HYP-mxc-017`).",
        ],
        "fdd_design": """### Bake pipeline (suite `FDD.md` §2.3, `US-04`)
* Scripts: `bake_production_adpa_image.ps1` (`AC-04.2`), `audit_production_image.ps1` (`AC-04.1`).
* Output VHDX: `winserv2025-prod-adpa.vhdx` with ADPA/SIDPA Windows service on `:8080`.
* After smoke and DB handle close: checkpoint `baseline-hot-ready`.
* Developer lineage remains on `winserv2025-mxc-dev.vhdx` (`img-mxc-dev-v2.3`).

### Documentation-only until bake completes
Supply-chain signing (`HYP-mxc-017`) has no implementation in tree today.
""",
        "fdd_errors": [
            ("Audit finds forbidden toolchain", "Fail bake gate; do not register image in production pool"),
            ("Prod pool pointed at dev VHDX", "Reject pool registration; cite `BRU-003-01`"),
        ],
        "stories": [
            (
                "3.1 — Clean production VHDX",
                "Software Release Engineer",
                "audit a baked production VHDX",
                "production carries no developer debris",
                [
                    "Given `winserv2025-prod-adpa.vhdx`, when audit runs, then Scoop, uv, cargo, git, compilers, and source repos are absent (`AC-04.1`).",
                ],
            ),
            (
                "3.2 — Warm baseline checkpoint",
                "Software Release Engineer",
                "bake and checkpoint the production image",
                "first wake avoids JIT compile stall",
                [
                    "Given bake completes, when service answers smoke on `localhost:8080/health`, then DB handles are closed and `baseline-hot-ready` is captured (`AC-04.2`).",
                ],
            ),
        ],
    },
    {
        "n": "004",
        "slug": "paused-ram-standby",
        "title": "Paused RAM standby, trimmed before suspend",
        "bdr": "BDR-01",
        "suite_us": "US-03",
        "brd_need": (
            "Idle guests must stop burning processor time while staying ready to resume within 300 ms. "
            "RAM and image disks remain allocated as a standing cost."
        ),
        "brus": [
            ("BRU-004-01", "Paused standby guests measure 0.0% host CPU.", "ADR-004 §4.2"),
            ("BRU-004-02", "Paused standby guests measure 0.0% host GPU; absent partition counts as 0 with note.", "ADR-004 §4.3"),
            ("BRU-004-03", "Guest memory stays resident; 0 MB reading means Saved/Stopped, not Paused.", "ADR-004 §4.4"),
            ("BRU-004-04", "Working set trimmed before `Suspend-VM`; target about 1.0–1.2 GB (`BEN-10`).", "ADR-004 §4.4"),
            ("BRU-004-05", "`Resume-VM` completes within 300 ms without paging working set from disk.", "ADR-004 §4.5"),
            ("BRU-004-06", "Parent VHDX and session `.avhdx` stay allocated while Paused.", "ADR-004 §4.7"),
        ],
        "metrics": [
            ("0.0% CPU on 10 standby VMs", "Claimed in implementation plan; not re-measured here (`AC-03.1`)"),
            ("GPU reading", "No prior sample; first reading is the test"),
            ("Paused RAM 1.0–1.2 GB vs under-700 MB lessons note", "Two figures; one must be chosen for `BEN-10`"),
        ],
        "oos": [
            "800 ms caller TTFB (`ADR-002`).",
            "Warm checkpoint contents (`ADR-003`).",
            "NVMe deep tier (`HYP-mxc-018` horizon).",
        ],
        "fdd_design": """### Pause and resume (`FDD.md` §2.2, `wxc-exec`)
* Trim working set (`EmptyWorkingSet` or `/admin/pre-trim`) while vCPUs run, then `Suspend-VM`.
* `Resume-VM` on lease; pages remain in host RAM.
* `pool-release` restores `baseline-hot-ready` then suspends so paused size equals checkpoint size when restore succeeds.

### States excluded
`Save-VM` and `Stopped` are not the warm standby path for this ADR.
""",
        "fdd_errors": [
            ("Resume waits on disk page-in", "Fail `HYP-mxc-002`; do not claim 300 ms ceiling"),
            ("Balloon trim after pause", "Invalid; trim must occur before `Suspend-VM`"),
        ],
        "stories": [
            (
                "4.1 — Zero idle CPU",
                "Infrastructure Platform Engineer",
                "keep dormant VMs Paused",
                "idle guests consume no processor",
                [
                    "Given 10 standby VMs Paused, when host CPU is read, then total CPU for those guests is 0.0% (`AC-03.1`).",
                ],
            ),
            (
                "4.2 — Trimmed paused footprint",
                "Infrastructure Platform Engineer",
                "trim before suspend",
                "paused guests hold a lean RAM allocation",
                [
                    "Given release restores `baseline-hot-ready` then suspends, when RAM is measured, then footprint is about 1.0–1.2 GB and the configured target is recorded (`AC-03.2`, `BEN-10`).",
                ],
            ),
            (
                "4.3 — Sub-300 ms resume",
                "Infrastructure Platform Engineer",
                "resume a Paused guest",
                "wake stays inside the platform ceiling",
                [
                    "Given ingress dispatches wake, when `Resume-VM` completes, then elapsed time ≤ 300 ms (`AC-03.3`).",
                ],
            ),
        ],
    },
    {
        "n": "005",
        "slug": "transient-differencing-disk",
        "title": "Transient differencing disk and egress whitelist",
        "bdr": "BDR-04",
        "req": "REQ-BDR-02, REQ-BDR-03",
        "suite_us": "US-02",
        "brd_need": (
            "Session residue must not survive release. Persistent data uses approved internal endpoints only."
        ),
        "brus": [
            ("BRU-005-01", "Session writes occur only on a transient `.avhdx` anchored at `baseline-hot-ready`.", "ADR-005 §4.1–4.2"),
            ("BRU-005-02", "Whole-guest or `.avhdx`-only discard both reproduce the next session from the approved production image.", "ADR-005 §4.3–4.4"),
            ("BRU-005-03", "Public internet egress is denied; named internal ports are allowed.", "ADR-005 §4.5"),
            ("BRU-005-04", "Hung requests past 900 s return HTTP 504 and trigger reap (distinct from wake 504).", "ADR-005 §4.6"),
        ],
        "metrics": [
            ("Session file gone after release", "Formulated (`HYP-mxc-013`); packet capture for ACL not renewed"),
            ("Parent hash unchanged (`AC-02.2`)", "Formulated"),
            ("Both discard paths (`BEN-12`)", "Open while production image unfinished"),
        ],
        "oos": [
            "Entropy reseed, clock step, DB pool purge on wake (`ADR-006`).",
            "Ingress TTFB (`ADR-002`).",
            "Memory scratch disk horizon (`HYP-mxc-019`).",
        ],
        "fdd_design": """### Differencing disk lifecycle (`FDD.md` §2.2)
* Lease: active `.avhdx` on `baseline-hot-ready`.
* Release or 300 s idle with `active_open_requests == 0`: delete `.avhdx`, restore checkpoint.
* Optional whole-guest removal reproduces from approved parent (`HYP-mxc-022`).

### Egress whitelist (guest firewall)
* Ingress: `:8080` from proxy only.
* Egress allow: `:1433`, `:5432`, private blob `:443`, `:53`, `:88`.
* Default deny public internet.
""",
        "fdd_errors": [
            ("Session file remains after release", "Fail `AC-02.1` / `BEN-07`"),
            ("Egress to public IP", "Drop and log; fail `AC-02.3`"),
        ],
        "stories": [
            (
                "5.1 — Ephemeral session disk",
                "CISO",
                "run a session that writes disk state",
                "no residue remains after release",
                [
                    "Given files written on `.avhdx`, when session ends or 300 s idle with no open requests, then `.avhdx` is deleted (`AC-02.1`).",
                    "Given parent `winserv2025-prod-adpa.vhdx`, when SHA-256 compared before and after, then hash is unchanged (`AC-02.2`).",
                ],
            ),
            (
                "5.2 — Egress whitelist",
                "CISO",
                "control guest outbound traffic",
                "only approved internal endpoints are reachable",
                [
                    "Given active guest, when connection targets public internet, then it is dropped (`AC-02.3`).",
                    "Given SQL, PostgreSQL, private blob, DNS, and Kerberos to approved endpoints, then connections are allowed.",
                ],
            ),
            (
                "5.3 — Discard and reproduce",
                "SecOps Engineer",
                "end a session by two discard paths",
                "the next session does not inherit the previous disk",
                [
                    "Given Path A whole-guest removal, when next guest is provisioned, then parent is approved production image (`BEN-12`).",
                    "Given Path B `.avhdx` only, when next session starts, then parent is still approved production image and guest may remain.",
                ],
            ),
        ],
    },
    {
        "n": "006",
        "slug": "watermark-pool",
        "title": "Watermark pool, replenish, and wake hygiene",
        "bdr": "Elasticity (REQ-BDR-05)",
        "req": "REQ-BDR-05",
        "suite_us": "US-05",
        "brd_need": (
            "Bursts must not cold-boot the next caller. The pool refills in about 1.5 seconds and runs hygiene before traffic."
        ),
        "brus": [
            ("BRU-006-01", "Leasing the last ready guest triggers background promotion to `StandbyPaused` in about 1.5 s.", "ADR-006 §4.2"),
            ("BRU-006-02", "Surge expands toward configured K_max; the check records whether 5 rps or 10 rps/5 s was configured.", "ADR-006 §4.3"),
            ("BRU-006-03", "First `/health` after wake reports entropy reseed, clock sync, and DB pools cleared.", "ADR-006 §4.5"),
            ("BRU-006-04", "Surplus guests leave after configured idle time; check records 300 s or 180 s.", "ADR-006 §4.6"),
            ("BRU-006-05", "Forecast pre-warm stays future (`HYP-mxc-020`); explicit `mxc-pool-warm` is allowed.", "ADR-006 §4.4"),
        ],
        "metrics": [
            ("Refill latency", "About 1.5 s in suite; not captured in new run (`BEN-09`)"),
            ("Surge threshold", "Two figures documented; `BEN-09` cannot pass until one is chosen"),
            ("Cooldown", "180 s in `AC-05.4` vs 300 s in `HYP-mxc-014`; check must record which applied"),
        ],
        "oos": [
            "Paused RAM size per guest (`ADR-004`).",
            "`.avhdx` discard rules (`ADR-005`).",
            "Forecast model (`HYP-mxc-020` horizon).",
        ],
        "fdd_design": """### Pool controller (`FDD.md` §2.2)
* States: `ColdProvisioned` → `StandbyPaused` → `ActiveRunning`.
* `pool_config.json`: `min_ready_standby`, `max_ready_standby`, `surge_velocity_threshold_rps` (example 10), queue depth trigger.
* Async worker promotes next guest after lease (`AC-05.1`).
* Pre-warm: `mxc-pool-warm --target prod-adpa --count N` / `POST /pool/warm` (`AC-05.3`).

### Wake hygiene on `/health` (`FDD.md` §2.3, `AC-02.4`)
1. PRNG reseed from hardware.
2. Guest clock within 50 ms of host UTC.
3. Database connection pools cleared.
""",
        "fdd_errors": [
            ("Ready pool empty under surge", "Expand toward K_max; do not cold-provision caller without recording threshold"),
            ("/health before hygiene complete", "Do not accept traffic; sign-in and TLS depend on clock step (`ADR-002`)"),
        ],
        "stories": [
            (
                "6.1 — Buffer replenishment",
                "SRE",
                "lease the last ready guest",
                "the next caller finds a Paused standby without blocking the in-flight request",
                [
                    "Given K_min met, when a guest is leased, then another reaches `StandbyPaused` in about 1.5 s in background (`AC-05.1`).",
                ],
            ),
            (
                "6.2 — Surge expansion",
                "SRE",
                "handle request bursts",
                "concurrent callers avoid cold boot",
                [
                    "Given configured surge threshold (record 5 rps or 10 rps/5 s), when tripped or queue depth > 0, then ready count expands up to K_max (`AC-05.2`, `BEN-09`).",
                ],
            ),
            (
                "6.3 — Wake hygiene",
                "SRE",
                "wake a guest from checkpoint",
                "cryptography, time, and DB pools are safe before traffic",
                [
                    "Given restore from `baseline-hot-ready`, when `/health` first succeeds, then entropy reseeded, clock synced, and DB pools cleared (`AC-02.4`).",
                ],
            ),
            (
                "6.4 — Scale down",
                "SRE",
                "cool surplus guests",
                "host RAM returns toward baseline",
                [
                    "Given traffic normalized, when idle exceeds configured cooldown (record 180 s or 300 s), then surplus above K_min is reaped (`AC-05.4`).",
                ],
            ),
        ],
    },
]


def brd_yaml(n: str, title: str) -> str:
    return f"""---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "{BASELINE}"
lifecycle_stage: "Stage 7 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-{n}-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-{n}-*.md"
---
"""


def fdd_yaml(n: str, slug: str) -> str:
    return f"""---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "{BASELINE}"
lifecycle_stage: "Stage 7 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-{n}-{slug}.md"
  - "docs/project-docs/Business-Requirements/BRD-{n}-{slug}.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-{n}-{slug}.md"
---
"""


def story_yaml(n: str, slug: str) -> str:
    return f"""---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "{BASELINE}"
lifecycle_stage: "Stage 7 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-{n}-{slug}.md"
  - "docs/project-docs/Business-Requirements/BRD-{n}-{slug}.md"
  - "docs/07-architecture/ADR-{n}-{slug}.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-{n}-{slug}.md"
---
"""


def write_brd(p: dict) -> None:
    n, slug, title = p["n"], p["slug"], p["title"]
    path = BRD_DIR / f"BRD-{n}-{slug}.md"
    lines = [
        brd_yaml(n, title),
        f"# BRD-{n}: {title}\n",
        "> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  ",
        "> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 7 (Requirement: Business)`  ",
        f"> **Inputs:** [ADR-{n}](../../07-architecture/ADR-{n}-{slug}.md), suite [BDR.md](../../hyperv/architecture/BDR.md) ({p.get('bdr', 'see ADR')})  ",
        "> **Process:** Define functional and non-functional business requirements and stakeholder rules  ",
        f"> **Outputs:** BRD-{n}-{slug}.md\n",
        f"**Source ADR:** [ADR-{n}](../../07-architecture/ADR-{n}-{slug}.md) — Accepted ({ADR_ACCEPT}).  ",
        f"**Governing Baseline:** `{BASELINE}`  ",
        "**Status:** Draft — business rules derived from an Accepted ADR; `approve-brd` has not been run.  ",
        "**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.\n",
        "## Business Need\n",
        p["brd_need"] + "\n",
        "## Business Rules (BRU)\n",
    ]
    for bru_id, text, cite in p["brus"]:
        lines.append(f"- **{bru_id}**: {text} *(from {cite})*")
    lines.append("\n## Stakeholder Success Metrics\n")
    lines.append("| Metric | Current state |")
    lines.append("|---|---|")
    for m, state in p["metrics"]:
        lines.append(f"| {m} | {state} |")
    lines.append("\n## Traceability to architecture suite\n")
    if p.get("req"):
        lines.append(f"- Requirements matrix: `{p['req']}` in [BDR.md](../../hyperv/architecture/BDR.md).")
    if p.get("suite_us"):
        lines.append(f"- Primary user story anchor: `{p['suite_us']}` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).")
    lines.append("\n## Out of Scope\n")
    for item in p["oos"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_fdd(p: dict) -> None:
    n, slug, title = p["n"], p["slug"], p["title"]
    path = FDD_DIR / f"FDD-{n}-{slug}.md"
    err_rows = "\n".join(f"| {a} | {b} |" for a, b in p["fdd_errors"])
    lines = [
        fdd_yaml(n, slug),
        f"# FDD-{n}: {title}\n",
        "> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  ",
        "> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 7 (Requirement: Solution)`  ",
        f"> **Inputs:** [ADR-{n}](../../07-architecture/ADR-{n}-{slug}.md), [BRD-{n}](../Business-Requirements/BRD-{n}-{slug}.md)  ",
        "> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  ",
        f"> **Outputs:** FDD-{n}-{slug}.md\n",
        f"**Source ADR:** [ADR-{n}](../../07-architecture/ADR-{n}-{slug}.md) — Accepted.  ",
        f"**Source BRD:** [BRD-{n}](../Business-Requirements/BRD-{n}-{slug}.md)  ",
        f"**Governing Baseline:** `{BASELINE}`  ",
        "**Status:** Draft — technical design aligned with suite [FDD.md](../../hyperv/architecture/FDD.md); `approve-fdd` has not been run.\n",
        "## Design\n",
        p["fdd_design"].strip() + "\n",
        "## Error Handling / Compatibility\n",
        "| Condition | Behavior |",
        "|---|---|",
        err_rows + "\n",
        "## Out of Scope\n",
    ]
    for item in p["oos"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_epic(p: dict) -> None:
    n, slug, title = p["n"], p["slug"], p["title"]
    path = STORY_DIR / f"epic-{n}-{slug}.md"
    lines = [
        story_yaml(n, slug),
        f"# Epic {n}: {title}\n",
        "> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  ",
        "> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 7 (Requirement: Story)`  ",
        f"> **Inputs:** [FDD-{n}](../project-docs/Functional-Design/FDD-{n}-{slug}.md), [BRD-{n}](../project-docs/Business-Requirements/BRD-{n}-{slug}.md), [ADR-{n}](../07-architecture/ADR-{n}-{slug}.md)  ",
        "> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  ",
        f"> **Outputs:** epic-{n}-{slug}.md\n",
        f"**Source ADR:** [ADR-{n}](../07-architecture/ADR-{n}-{slug}.md) — Accepted.  ",
        f"**Source BRD/FDD:** [BRD-{n}](../project-docs/Business-Requirements/BRD-{n}-{slug}.md) / [FDD-{n}](../project-docs/Functional-Design/FDD-{n}-{slug}.md)  ",
        f"**Governing Baseline:** `{BASELINE}`  ",
        "**Status:** Draft — stories trace to suite acceptance criteria where they exist; `approve-user-stories` has not been run.\n",
    ]
    if p.get("suite_us"):
        lines.append(
            f"**Suite anchor:** [{p['suite_us']}](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.\n"
        )
    for sid, role, want, so_that, acs in p["stories"]:
        lines.append(f"## Story {sid}\n")
        lines.append(
            f"**Status:** Ready for review — not yet run through `implement-story`  "
        )
        lines.append(
            f"**As a** {role}, **I want** {want}, **so that** {so_that}.\n"
        )
        lines.append("**Acceptance Criteria:**")
        for ac in acs:
            lines.append(f"- {ac}")
        lines.append("")
    lines.append("## Before running `implement-story`\n")
    lines.append(
        "Run `validate-intent-foundation` when the project enables it. "
        "Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).\n"
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    BRD_DIR.mkdir(parents=True, exist_ok=True)
    FDD_DIR.mkdir(parents=True, exist_ok=True)
    STORY_DIR.mkdir(parents=True, exist_ok=True)
    for pack in PACKS:
        write_brd(pack)
        write_fdd(pack)
        write_epic(pack)
        print(pack["n"], pack["slug"])


if __name__ == "__main__":
    main()
