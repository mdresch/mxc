from pathlib import Path

WIKI = Path(
    r"C:\Users\menno\Documents\Second Brain\wiki\Projects\MXC\01 Architecture Decisions (ADR)"
)
GATE = Path(r"D:\Source\repos\mxc\docs\project-docs\gates")

for path in sorted(WIKI.glob("ADR-00*.md")):
    num = path.name.split("-")[1]
    text = path.read_text(encoding="utf-8")
    text = text.replace('status: "Proposed"', 'status: "Accepted"')
    text = text.replace(
        "**Governing Baseline:** `PMP-BL-v1.0.0`. `approve-adr` has not been run. This note is not an approved baseline.",
        "**Governing Baseline:** `PMP-BL-v1.0.0`. This note is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.",
    )
    old_status = (
        "**Proposed (2026-10-30)** — awaiting explicit review under `approve-adr` (`mxc-governance`). "
        "The architecture-suite record is marked Accepted. That mark is not this note's sign-off. "
        "A recommendation from `approve-adr`, once run, is an input to the decision and does not replace it."
    )
    gate = GATE / f"approve-adr-{num}-2026-10-30.adjudication.json"
    new_status = (
        "**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 "
        "(policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). "
        f"Gate record: `{gate}`."
    )
    text = text.replace(old_status, new_status)
    path.write_text(text, encoding="utf-8")
    print(path.name)
