"""Generate Executive Summary Document (.docx and .pdf) for MXC.

Applies the official enterprise layout, palette, and styling defined in
scripts/hyperv/generate_architecture_docx.py:
- Deep Navy / Steel Blue: #1F4E79 (Calibri 22pt title, 15pt H1, 12.5pt H2, table headers)
- Neutral Slate / Gray: #595959 / #333333 (Calibri 10.5pt body, line spacing 1.15)
- Callout block: #F2F4F7 fill with 3pt #1F4E79 left accent border
- Styled Tables: #1F4E79 header fill with white text, alternating #FFFFFF/#F6F8FA rows, #D0D7DE borders
- Margins: 0.85 inches
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor
import win32com.client


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def set_cell_shading(cell, color_hex: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, color="D0D7DE") -> None:
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/></w:tblBorders>'
    )
    tblPr.append(borders)


def add_h1(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)


def add_h2(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(12.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(40, 40, 40)


def add_body(doc, text: str, bold_prefix: str | None = None) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = "Calibri"
        rb.font.size = Pt(10.5)
        rb.font.bold = True
        rb.font.color.rgb = RGBColor(40, 40, 40)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(51, 51, 51)


def add_callout(doc, text: str, title: str = "STRATEGIC ARCHITECTURAL ENHANCEMENT:") -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, "F2F4F7")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="1F4E79"/>'
        f'<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>'
    )
    tcPr.append(borders)
    cp = cell.paragraphs[0]
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(2)
    cp.paragraph_format.line_spacing = 1.15
    cr1 = cp.add_run(title + "\n")
    cr1.font.name = "Calibri"
    cr1.font.size = Pt(10)
    cr1.font.bold = True
    cr1.font.color.rgb = RGBColor(31, 78, 121)
    cr2 = cp.add_run(text)
    cr2.font.name = "Calibri"
    cr2.font.size = Pt(10)
    cr2.font.italic = True
    cr2.font.color.rgb = RGBColor(70, 70, 70)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_styled_table(doc, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, "D0D7DE")

    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        set_cell_shading(cell, "1F4E79")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for i, row in enumerate(rows):
        bg = "FFFFFF" if i % 2 == 0 else "F6F8FA"
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if j == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(51, 51, 51)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build_document() -> docx.Document:
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Document Header / Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("Executive Architecture Summary")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(31, 78, 121)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run("High-Density Standby Stand-Up, Sub-300ms Resume & Golden Bake RAM Optimization")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGBColor(89, 89, 89)

    # Metadata Block
    meta_headers = ["Project", "Document Baseline", "Author / Architect", "Classification", "Date"]
    meta_rows = [
        ["MXC Micro-Execution Container", "PMP-BL-v1.0.0 (Phase 1 / SPARK-vNext)", "Menno Drescher", "Internal Enterprise Technical Brief", "November 21, 2026"]
    ]
    add_styled_table(doc, meta_headers, meta_rows)

    # 1. Executive Brief
    add_h1(doc, "1. Executive Brief & Strategic Objective")
    add_body(
        doc,
        "The primary architectural challenge of the MXC platform is delivering Type-1 Hyper-V hardware-level security "
        "and Windows API fidelity (WMI, COM+, Win32 subsystems) while eliminating the latency and resource penalties of traditional "
        "virtual machines. Standard Windows Server cold boot cycles require 14 to 45 seconds, while unmanaged idle instances continuously "
        "drain host processor capacity and licensing limits."
    )
    add_body(
        doc,
        "By orchestrating an immutable golden image bake, an intelligent connection-buffering reverse proxy, and a pre-warmed Paused RAM "
        "standby fleet, MXC guarantees:",
        "Core Platform Guarantees: "
    )
    add_body(doc, "All dormant standby guests maintain 0.0% host CPU and 0.0% GPU consumption (AC-03.1, BRU-004-01).", "• 0.0% Idle Compute Cost: ")
    add_body(doc, "Hardware unpause from host RAM completes in <= 300 ms (AC-03.3, nominal ~215 ms).", "• Sub-300ms Hypervisor Resume: ")
    add_body(doc, "Total end-to-end client cold-wake Time to First Byte stays strictly under 800 ms with <= 5 ms warm overhead (AC-01.1, AC-01.2).", "• Sub-800ms Caller TTFB: ")
    add_body(doc, "Production VHDX images are audited to guarantee 100% absence of compilers, tools, or source debris (AC-04.1).", "• Clean Production Supply Chain: ")

    # 2. Sub-300ms Resume & Predictive Ingress
    add_h1(doc, "2. Sub-300ms Hyper-V Resume & Predictive Ingress Interception")
    add_body(
        doc,
        "In MXC, standby virtual machines reside in the Hyper-V Paused state (entered via Suspend-VM). Because guest memory pages "
        "remain resident in physical host RAM, Resume-VM unpauses the guest vCPUs in ~215 ms without paying disk page-in penalties. "
        "Alternative states such as Saved-VM or cold boot require reading gigabytes from disk, blowing past the 300 ms ceiling and "
        "exposing callers to wake delays of 14–45 seconds."
    )
    add_callout(
        doc,
        "Rather than waiting for the entire HTTP request payload before dispatching Resume-VM, the ingress gateway intercepts early "
        "TLS ClientHello packets and Server Name Indication (SNI) hostnames during initial TCP connection establishment (IMP-MXC-002). "
        "This completely overlaps the ~220ms hypervisor wake with TLS handshake round-trips. When the client finishes encrypting the "
        "application request, the VM is already awake and listening on :8080, reducing perceived cold TTFB from ~350ms to ~120ms (near-warm).",
        "NEXT-PHASE INNOVATION: Early TLS ClientHello Predictive Resume (IMP-MXC-002)"
    )

    # 3. Golden Bake Pipeline
    add_h1(doc, "3. Golden Image Bake Pipeline & JIT Warm-Up Protocol")
    add_body(
        doc,
        "Production workloads must never run from developer disks carrying toolchains, package managers, or build staging artifacts (ADR-003, BRU-003-01). "
        "The automated bake pipeline enforces a zero-trust compliance gate (AC-04.1) verifying total absence of Scoop, uv, cargo, rustup, git, "
        "C++ compilers (cl.exe, link.exe, gcc.exe), and workspace staging folders."
    )
    add_body(
        doc,
        "Prior to snapshotting the immutable baseline-hot-ready checkpoint, the bake pipeline executes a synthetic health probe on "
        "localhost:8080/health (AC-04.2). This pre-warms application code, triggers JIT compilation, and exercises cryptography and time sync. "
        "Crucially, all database connection pools and network sockets are purged to zero (/admin/clear-pools) before checkpoint capture (LL-004), "
        "preventing stale socket leakage and broken pipe errors across future instances."
    )

    # 4. Standby RAM Sizing
    add_h1(doc, "4. Standby RAM Sizing: Challenging the 1.0–1.2 GB Floor")
    add_body(
        doc,
        "In Phase 1, standby guests are provisioned with a conservative 1.0–1.2 GB (1024–1228.8 MB) memory target (BEN-10). "
        "A rigorous empirical analysis of 64-bit Windows Server 2025 memory dynamics reveals that this baseline can be aggressively "
        "optimized to unlock dramatic fleet density improvements:"
    )
    add_body(
        doc,
        "Bare kernel, HAL, and Hyper-V synthetic bus drivers (vmbus.sys, storvsc.sys, netvsc.sys) reside in Non-Paged Pool (NPP), "
        "requiring ~200–280 MB that the Windows memory manager cannot page out. Compressing below 450 MB induces STATUS_NO_MEMORY BugChecks.",
        "• The Incompressible Non-Paged Pool Floor (~200–280 MB): "
    )
    add_body(
        doc,
        "If ballooning squeezes the VM below ~600 MB, the guest memory manager is forced to push ADPA service heap and .NET/Rust runtime "
        "assemblies into pagefile.sys. Upon unpause, the guest suffers a cascade of hard page faults (150–350 ms), shattering the <= 5 ms proxy overhead SLA.",
        "• The Pagefile Thrashing Trap on Wake: "
    )
    add_body(
        doc,
        "By replacing the Explorer shell with a direct console prompt (powershell.exe -NoLogo), permanently disabling consumer daemons "
        "(Search Indexer, Windows Update, Spooler), and applying Win32 EmptyWorkingSet() post-smoke with Hyper-V Dynamic Memory MinimumRAM = 512MB, "
        "the golden baseline can be packed to ~640 MB (0.625 GB) without risk of wake page thrashing (IMP-MXC-006).",
        "• The Safe Ultra-Lean Operating Floor (~640 MB): "
    )
    add_callout(
        doc,
        "Compressing the standby memory floor from 1.1 GB to 640 MB yields an ~80% increase in host standby density. "
        "A standard 64 GB host increases capacity from ~45 to ~80 concurrent standby micro-instances at zero additional infrastructure cost.",
        "FLEET DENSITY MULTIPLIER (IMP-MXC-006):"
    )

    # 5. Lifecycle Decoupling
    add_h1(doc, "5. Lifecycle Decoupling: Disposable vs. Recycled VMs")
    add_body(
        doc,
        "A critical architectural insight emerged regarding memory trimming: pre-suspend trimming is load-bearing only for the golden bake pipeline "
        "and recycled standby pool fleets (ADR-005 §4.2 differencing-disk discard) to prevent cross-session memory bloat. "
        "When operating under a pure disposable whole-guest model (ADR-005 §4.3), where the instance is destroyed immediately post-session (Remove-VM), "
        "in-session post-request trimming is redundant. Bypassing trim on teardown eliminates ~50–100 ms of session latency, while replenished standby instances "
        "spawn pre-trimmed directly from baseline-hot-ready (IMP-MXC-005, LL-005)."
    )

    # 6. Copilot Strategic Peer Review Synthesis
    add_h1(doc, "6. Strategic Architectural Refinements: Peer Review Synthesis")
    add_body(
        doc,
        "A technical architecture review conducted by Copilot affirmed that the next generation of the MXC platform should move beyond "
        "incremental guest trimming toward macroscopic refinements that maximize tenant density, predictability, attestation, and wake orchestration. "
        "Eight strategic priorities were identified for incorporation into Phase Next:"
    )

    add_body(
        doc,
        "Establish an intelligent 3-tier standby pool: Hot (Running, ~5ms resume, high-priority tenants), Warm (Paused in RAM, ~215ms resume, standard workloads), "
        "and Cold (Saved on NVMe, 2–5s resume, rare/batch workloads). Allocating 5–10% Hot, 25% Warm, and 65% Cold dynamically optimizes host economics, "
        "effectively doubling practical tenant density on large physical hosts (HYP-mxc-018 horizon).",
        "1. Multi-Tier Standby Pools (IMP-MXC-007): "
    )

    add_body(
        doc,
        "Evolve early TLS interception into temporal, calendar, and historical activity forecasting. By tracking shift start times, tenant usage history, "
        "and recurring workload schedules (e.g. daily 08:55 login peaks, monthly payroll runs), instances can be unpaused seconds prior to arrival, "
        "driving perceived cold-wake latency to 0 ms.",
        "2. Activity-Based Predictive Wake (IMP-MXC-008): "
    )

    add_body(
        doc,
        "Across 80+ running micro-instances, massive memory regions are identical (ntoskrnl.exe, CLR JIT caches, .NET runtime, user32.dll). "
        "Leveraging host-level Hyper-V Memory Combining / Page Sharing enables identical pages to be shared across guest partitions. "
        "This compresses a 640 MB logical allocation down to an estimated 300–450 MB effective physical host RAM—potentially surpassing the gains "
        "of internal guest trimming alone.",
        "3. Host Memory Deduplication & Page Sharing (IMP-MXC-009): "
    )

    add_body(
        doc,
        "Expand image signing into an unbroken cryptographic chain of custody: Source Git Commit -> Build Pipeline -> SPDX/CycloneDX SBOM Generation -> "
        "Image Hash -> Cosign/Sigstore Attestation -> Golden Snapshot -> Pre-Dispatch Verification Gate in PoolRegistrationGuard. "
        "Guarantees SLSA Level 3 supply chain compliance and tamper-proof production deployment (HYP-mxc-017 horizon).",
        "4. End-to-End Cryptographic Provenance (IMP-MXC-010): "
    )

    add_body(
        doc,
        "For high-density AMD EPYC and Intel Xeon Scalable hosts hosting 80+ guests, enforce NUMA-node affinity for VM memory allocations and "
        "wake dispatching. Prevents cross-socket memory bus saturation during simultaneous multi-tenant resume bursts.",
        "5. NUMA-Aware Placement & Affinity: "
    )

    add_body(
        doc,
        "Branch the single golden baseline into specialized immutable workload profiles: Gold-v1 -> .NET Core Profile, Rust Profile, Python/AI Profile. "
        "Delivers pre-warmed runtime affinity while retaining strict immutable checkpoint guarantees.",
        "6. Snapshot Version Graphs & Workload Profiles: "
    )

    add_body(
        doc,
        "Enhance the ingress reverse proxy with request classification, tenant fairness, and priority queuing. Premium tenants trigger immediate unpause, "
        "standard tenants enter buffered hold, and batch jobs trigger queued bulk unpauses, mirroring modern enterprise cloud edge routers.",
        "7. Connection Buffer Intelligence & Tenant QoS: "
    )

    add_body(
        doc,
        "Deploy a closed-loop economics controller that continuously evaluates cost-per-session, cost-per-wake, memory efficiency, and host saturation "
        "to autonomously decide tier depth, consolidation, and migration. Transforms MXC from an isolated VM engine into an autonomous execution fabric.",
        "8. Autonomous Fleet Economics Engine (IMP-MXC-011): "
    )

    # 7. Sizing & Benchmark Scorecard
    add_h1(doc, "7. Comparative Architecture Sizing & Benchmark Matrix")
    matrix_headers = ["Metric / Dimension", "Standard VM", "Phase 1 Baseline", "Phase Next Target", "Strategic Multiplier"]
    matrix_rows = [
        ["Cold Boot / Wake Latency", "14–45 seconds", "< 800 ms TTFB (~350ms)", "0 ms Perceived (Predictive)", "Activity Forecasting (IMP-MXC-008)"],
        ["Hypervisor Resume", "N/A (Cold Boot)", "~215 ms (<= 300ms SLA)", "~215 ms (<= 300ms SLA)", "Resident RAM unpause (AC-03.3)"],
        ["Idle Compute (CPU/GPU)", "2–5% idle polling", "Strictly 0.0% / 0.0%", "Strictly 0.0% / 0.0%", "Zero wasted processor cycles (AC-03.1)"],
        ["Logical Standby RAM", "2.5–4.0 GB", "1.0–1.2 GB (BEN-10)", "~512–640 MB (IMP-MXC-006)", "Prompt-only stripping (~80% density)"],
        ["Effective Host RAM / Guest", "2.5–4.0 GB", "1.0–1.2 GB", "300–450 MB (IMP-MXC-009)", "Hyper-V Memory Deduplication (2x-3x density)"],
        ["Standby Pool Architecture", "Single Static Tier", "Single Paused Tier", "Hot / Warm / Cold Tiers", "Multi-tier economics (IMP-MXC-007)"],
        ["Image Supply Hygiene", "Carries dev toolchain", "Strict Audit (AC-04.1)", "SLSA Level 3 Attestation", "Unbroken Cosign/Sigstore chain (IMP-MXC-010)"],
        ["Session Release Teardown", "N/A (Manual wipe)", "~120 ms (with trim)", "~20–30 ms (bypass trim)", "Fast disposable VM teardown (IMP-MXC-005)"],
    ]
    add_styled_table(doc, matrix_headers, matrix_rows)

    # 8. Top 5 SPARK-vNext Catalysts
    add_h1(doc, "8. Top 5 SPARK-vNext Catalysts & Implementation Roadmap")
    add_body(
        doc,
        "To maximize architectural leverage and enterprise business value in the next phase, the technical review recommends "
        "prioritizing five core initiatives for the SPARK-vNext work breakdown structure:"
    )
    catalysts_headers = ["Priority", "Initiative Title", "Strategic Value & Objective", "Target Outcome"]
    catalysts_rows = [
        ["1", "Predictive Wake Engine (IMP-MXC-008)", "Activity & schedule forecasting pre-warming instances moments before peak", "0 ms perceived wake latency"],
        ["2", "Memory Deduplication & Page Sharing (IMP-MXC-009)", "Host-level page sharing across 80+ identical Windows Server guests", "300–450 MB effective host RAM per guest"],
        ["3", "Signed Provenance Pipeline (IMP-MXC-010)", "Cryptographic Git-to-snapshot SBOM attestation and runtime verification gate", "SLSA Level 3 supply chain certification"],
        ["4", "Multi-Tier Standby Pool Architecture (IMP-MXC-007)", "Hot (5ms), Warm (200ms), and Cold (NVMe 2-5s) execution tiers", "Doubles practical tenant capacity per host"],
        ["5", "Autonomous Fleet Economics Scheduler (IMP-MXC-011)", "Dynamic feedback loop optimizing cost-per-session, wake, and host saturation", "Self-optimizing serverless execution fabric"],
    ]
    add_styled_table(doc, catalysts_headers, catalysts_rows)

    add_body(
        doc,
        "All initiatives are registered in Continuous-Improvement-Register.md and will be formally harvested during Stage 18 "
        "to seed the Intent Refinement Proposal and catalyst baseline for SPARK-vNext."
    )

    return doc


def main() -> None:
    docx_path = OUTPUT_DIR / "Executive-Summary-Sub-ms-Resume-and-Bake-RAM-Optimization.docx"
    pdf_path = OUTPUT_DIR / "Executive-Summary-Sub-ms-Resume-and-Bake-RAM-Optimization.pdf"

    print(f"[*] Building enterprise Word document at: {docx_path}...")
    doc = build_document()
    doc.save(str(docx_path))
    print(f"[+] Word document saved successfully ({docx_path.stat().st_size} bytes).")

    print(f"[*] Converting Word document to PDF via Word COM at: {pdf_path}...")
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        wb = word.Documents.Open(str(docx_path))
        # 17 = wdFormatPDF
        wb.SaveAs(str(pdf_path), FileFormat=17)
        wb.Close(False)
        print(f"[+] PDF document generated successfully ({pdf_path.stat().st_size} bytes).")
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
