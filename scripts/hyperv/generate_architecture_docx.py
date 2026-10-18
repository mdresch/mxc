"""
generate_architecture_docx.py - Generates formatted enterprise Word (.docx) documents
for the MXC Scale-to-Zero Hyper-V Production Architecture (ADPA / SIDPA).

Outputs formatted Word documents directly into docs/hyperv/architecture/docx/.
"""

import sys
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "hyperv" / "architecture" / "docx"

def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
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

def init_doc(title_text, subtitle_text):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title_text)
    r.font.name = "Calibri"
    r.font.size = Pt(22)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(14)
    r = p.add_run(subtitle_text)
    r.font.name = "Calibri"
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(89, 89, 89)
    return doc

def add_h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)

def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(12.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(40, 40, 40)

def add_body(doc, text, bold_prefix=None):
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
    return p

def add_code_block(doc, code_text, caption=None):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(2)
        cr = cp.add_run(caption)
        cr.font.name = "Calibri"
        cr.font.size = Pt(9.5)
        cr.font.bold = True
        cr.font.color.rgb = RGBColor(89, 89, 89)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, "F8F9FA")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="E1E4E8"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="E1E4E8"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="E1E4E8"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="E1E4E8"/></w:tcBorders>'
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    r = p.add_run(code_text)
    r.font.name = "Consolas"
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(36, 41, 46)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_callout(doc, text, title="FUTURE HORIZON & SCALING ENHANCEMENT:"):
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

def add_styled_table(doc, headers, rows):
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


def generate_master_add():
    doc = init_doc(
        "Architecture Design Document (ADD)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes for Enterprise Applications (ADPA / SIDPA)"
    )
    add_h1(doc, "1. Executive Summary")
    add_body(doc, "This Architecture Design Document (ADD) defines the unified enterprise specification for running production-grade services—specifically ADPA (Automated Dynamic Process Automation) and SIDPA (Secured Intelligent Data Processing Application)—inside hardware-isolated Windows Server 2025 Type-1 Hyper-V micro-instances.")
    add_body(doc, "When no client requests are active, production VMs remain suspended in RAM (Paused), consuming 0.0% CPU cycles and releasing paged memory via Hyper-V Dynamic Memory.", "• 0% Idle Resource Footprint: ")
    add_body(doc, "An intelligent Ingress Gateway buffers incoming client HTTP requests, triggers hardware unpause via the MXC control plane in <300ms, verifies socket readiness, and proxies the payload with zero perceptible cold-start delay (<600ms Time to First Byte).", "• Sub-Second Wake-on-Request: ")
    add_body(doc, "Upon session completion or inactivity timeout, the instance delta disk (.avhdx) is discarded, returning the VM back to a pristine, immutable checkpoint baseline (baseline-hot-ready) to prevent state drift and eliminate malware persistence.", "• Sterile Session Isolation: ")

    add_h1(doc, "2. Pillar Index")
    add_body(doc, "Business context, ROI drivers, cost metrics, high-level requirements matrix (REQ-BDR-01 to 04), and zero-trust security requirements.", "• Pillar I — Business Drivers & Requirements (BDR): ")
    add_body(doc, "Formal decision records (ADR-001 through ADR-005) justifying Hyper-V Type-1 virtualization, JIT wake-on-request proxies, separate production images, paused RAM standby states, and transient differencing disk rollback.", "• Pillar II — Architectural Decision Records (ADR): ")
    add_body(doc, "Component breakdown, JSON proxy route configuration, lifecycle state machines, wake-on-request sequence flows, and automated reaping protocols.", "• Pillar III — Functional Design Document (FDD): ")
    add_body(doc, "BDD/Gherkin user stories and testable acceptance criteria across End Users (US-01), SecOps (US-02), DevOps/SRE (US-03), and CI/CD Release Engineers (US-04).", "• Pillar IV — User Stories & Acceptance Criteria: ")

    add_h1(doc, "3. System Architecture Topology (Mermaid Specification)")
    add_code_block(doc, """flowchart TD
    subgraph Clients["Client Layer"]
        User["Enterprise End User / REST API Client"]
        ChatAgent["Eve Chat Agent / Automated Orchestrator"]
    end

    subgraph Ingress["Ingress & Edge Routing Layer"]
        Proxy["JIT Ingress Reverse Proxy Gateway (:443)"]
        BufferQueue["Request Connection Buffer / Hold Queue"]
        AuthZ["Mutual TLS & JWT Authentication"]
    end

    subgraph ControlPlane["MXC Hardware Virtualization Control Plane"]
        FastMCP["MXC FastMCP Server (:8000)"]
        PoolManager["Warm Standby Pool Manager (wxc-exec)"]
        Reaper["Idle Inactivity Reaper (5 min timeout)"]
    end

    subgraph HyperVHost["Hyper-V Server 2025 Host (Machine A)"]
        Switch["Internal vSwitch (Isolated Port Forwarding)"]
        ActiveVM["Active Leased VM (hv:prod-adpa-01) | Running"]
        StandbyVM["Standby VM (hv:prod-adpa-02) | Paused (0% CPU)"]
        GoldenProdVHDX[("Production Base VHDX (winserv2025-prod-adpa.vhdx)")]
        SnapshotBaseline[("Clean Memory Checkpoint (baseline-hot-ready.avhdx)")]
    end

    User --> Proxy --> AuthZ --> BufferQueue
    ChatAgent --> Proxy
    BufferQueue -- "Wake Signal if dormant" --> FastMCP --> PoolManager
    PoolManager -- "Resume-VM (<300ms)" --> StandbyVM -.-> ActiveVM
    BufferQueue -- "Forward HTTP" --> Switch --> ActiveVM
    Reaper -- "Inactivity timeout" --> PoolManager -- "Discard .avhdx & Restore" --> ActiveVM""")

    add_h1(doc, "4. Technical Feasibility & Metric Comparison")
    add_styled_table(
        doc,
        ["Dimension", "Cold-Booted VM", "Always-On VM", "MXC JIT Scale-to-Zero (This Architecture)"],
        [
            ["Idle CPU Usage", "0% (Offline)", "2% – 8% per VM continuous", "0.0% (Paused in Hypervisor)"],
            ["Time to First Byte (Wakeup)", "25,000ms – 45,000ms", "5ms – 10ms", "350ms – 650ms (<=800ms SLA)"],
            ["Subsequent Request Latency", "5ms – 10ms", "5ms – 10ms", "5ms – 10ms (<=15ms SLA)"],
            ["Memory Isolation Level", "Hardware Type-1", "Hardware Type-1", "Hardware Type-1 (VT-x / AMD-V / SLAT)"],
            ["Post-Session State Drift", "Vulnerable to drift", "Accumulates dirty state", "Zero (Automated Checkpoint Rollback)"],
            ["Host Density (Per 64GB RAM)", "~25 (Not running)", "~8 (Bottlenecked)", "30+ Instances Concurrent"]
        ]
    )

    add_callout(
        doc,
        "1. Multi-Region Hypervisor Mesh: Expand the MXC Rust control plane across geo-distributed bare-metal Hyper-V clusters paired with Anycast DNS edge proxies to guarantee <100ms global ingress socket acceptance.\n"
        "2. Carbon-Aware Workload Scheduling: Dynamically shift suspended VM resume operations and background image baking pipelines to data centers operating at peak renewable energy availability.\n"
        "3. Confidential Computing Partitions: Integrate hardware-enforced memory encryption (AMD SEV-SNP / Intel TDX) at the Hyper-V guest partition level for cryptographic isolation even against host-level inspection."
    )
    return doc


def generate_bdr():
    doc = init_doc(
        "Pillar I: Business Drivers & Requirements (BDR)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    add_h1(doc, "1. Executive Context & Operational Trilemma")
    add_body(doc, "Enterprises deploying automated processing services (such as ADPA and SIDPA) face a critical operational trilemma across cost, latency, and security:")
    add_body(doc, "Traditional deployments maintain dedicated, always-on virtual machines to avoid slow startup times. A cluster of 10–20 always-on Windows Server instances consumes significant host CPU ticks, saturates hypervisor RAM, and incurs 24/7 compute and licensing costs even during idle nights and weekends.", "1. High Infrastructure & Idle Power Costs: ")
    add_body(doc, "When traditional virtual machines are shut down (Stopped) to save resources, waking them upon an incoming HTTP request takes 25 to 45 seconds, leading to HTTP 504 gateway timeouts and failed webhooks.", "2. Unacceptable Cold-Boot Delays: ")
    add_body(doc, "While Linux containers achieve fast spin-up, they share the host kernel. High-compliance workloads processing confidential financial data, PII, or proprietary AI weights require a true Type-1 Hypervisor hardware boundary (Hyper-V Ring-0 isolation).", "3. Inadequate Security in Shared Container Runtimes: ")

    add_h1(doc, "2. Core Business Drivers (Strategic Goals)")
    add_h2(doc, "BDR-01: Maximum Resource Density & Cost Reduction (Scale-to-Zero)")
    add_body(doc, "Minimize hardware footprint and operating costs by ensuring that when zero client requests are pending, virtual machine instances consume 0% CPU and release idle memory pages.", "Goal: ")
    add_body(doc, "0.0% Host CPU consumption during idle periods; >= 65% compression in active hypervisor memory commitment via Dynamic Memory paging; support for 3x to 5x more concurrent registered services per physical host.", "Target Metrics: ")
    add_callout(doc, "Predictive Auto-Warming & Same-Page Merging: Introduce machine learning ingress forecasting models that analyze historical tenant traffic patterns to proactively resume anticipated pools 5 seconds before traffic surges occur, paired with hypervisor memory deduplication (Kernel Same-Page Merging) and Carbon-Aware scheduling across green data centers.")

    add_h2(doc, "BDR-02: Strict Sub-Second Response SLAs (Instantaneous Readiness)")
    add_body(doc, "Provide instantaneous, consumer-grade responsiveness to end users and API integrations without manual provisioning.", "Goal: ")
    add_body(doc, "Time to First Byte (TTFB) from a completely dormant/paused state under 800ms (typically 350ms – 550ms); subsequent warm request latency under 15ms.", "Target Metrics: ")
    add_callout(doc, "Global Edge Socket Holding (Anycast PoPs): Deploy a globally distributed edge proxy mesh that accepts TLS handshakes and holds incoming client sockets at the closest regional Point of Presence (PoP) while concurrently dispatching high-speed gRPC wake signals to the Hyper-V bare-metal pool.")

    add_h2(doc, "BDR-03: Zero-Trust Hardware-Grade Isolation")
    add_body(doc, "Guarantee cryptographic and hardware-level isolation for every processing session so that cross-tenant side-channel leakage or kernel compromise is mathematically prevented.", "Goal: ")
    add_body(doc, "Dedicated Virtual Processor (vCPU) and Second-Level Address Translation (SLAT / Intel VT-x / AMD-V) hardware isolation; zero shared kernel space between the application workload, other VMs, or the Hyper-V host OS.", "Target Metrics: ")
    add_callout(doc, "Hardware-Enforced Confidential Computing: Implement AMD SEV-SNP (Secure Encrypted Virtualization - Secure Nested Paging) and Intel TDX at the Hyper-V partition level, ensuring that guest RAM contents remain encrypted in hardware and unreadable even by host administrators or physical memory introspectors.")

    add_h2(doc, "BDR-04: Immutable State & Zero-Persistence Guarantee")
    add_body(doc, "Eliminate configuration drift, accumulated file-system debris, and the risk of persistent malware or cross-session data contamination between client runs.", "Goal: ")
    add_body(doc, "100% automated restoration to a pristine, cryptographically verifiable baseline snapshot (baseline-hot-ready) upon session release; differencing disk deltas (.avhdx) discarded immediately upon session termination.", "Target Metrics: ")
    add_callout(doc, "Cryptographic Ephemeral Scrubbing: Pair .avhdx delta discard operations with per-session ephemeral disk encryption keys that are destroyed in RAM upon session release, guaranteeing cryptographic erasure prior to storage block reclamation.")

    add_h1(doc, "3. High-Level Requirements Matrix")
    add_styled_table(
        doc,
        ["Requirement ID", "Category", "Requirement Description", "Success Verification"],
        [
            ["REQ-BDR-01", "Performance", "Ingress gateway must buffer incoming requests and wake dormant VM in <300ms (<= 800ms total TTFB).", "Measured gateway latency logs <= 300ms to VM resume and socket connect."],
            ["REQ-BDR-02", "Lifecycle", "Instances with no traffic for >300s must automatically revert to baseline and suspend.", "Verified automated snapshot rollback and Hyper-V Paused state transition."],
            ["REQ-BDR-03", "Security", "Guest application must communicate strictly via an isolated virtual network segment.", "Network traffic restricted to Ingress Gateway port forwarding (:8080); no unauthorized egress."],
            ["REQ-BDR-04", "Packaging", "Production image must exclude developer toolchains, debuggers, and source repositories.", "Verified clean golden base image (winserv2025-prod-adpa.vhdx) containing only pre-jitted production binaries and hardened OS."]
        ]
    )
    return doc


def generate_adr():
    doc = init_doc(
        "Pillar II: Architectural Decision Records (ADR)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    adr_items = [
        (
            "ADR-001: Selection of Type-1 Hyper-V Virtualization over Container Namespaces",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "Enterprise automation workloads (ADPA and SIDPA) require running Windows-native services, COM+ dependencies, WMI, Windows Performance Counters, and Group Policy Objects (GPO) that are unsupported or unstable inside container namespaces. We evaluated Windows Server Containers vs. Hyper-V Generation 2 Type-1 Virtual Machines.",
            "Standardize on Type-1 Hyper-V Generation 2 Virtual Machines orchestrated by the native Rust control plane (wxc-exec --features hyperv). Hyper-V partitions utilize Intel VT-x / AMD-V and Second-Level Address Translation (SLAT), providing a verifiable hardware boundary and deterministic memory checkpointing.",
            "Positive: Total isolation, cryptographic immutability, full Windows Server API compatibility. Trade-off: Requires a Windows Pro, Enterprise, or Windows Server host with Hyper-V enabled.",
            "Hyper-V Direct Micro-VM Partitions: Explore integration with stripped-down Hyper-V micro-VM profiles and custom minimal Windows Server Core footprints to reduce baseline memory commitment per suspended instance from 1GB down to <256MB."
        ),
        (
            "ADR-002: Just-in-Time (JIT) Connection-Buffering Ingress Gateway",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "End users and upstream webhooks send standard HTTPS requests to public endpoints (e.g., https://adpa.internal.company.com/api/v1/process). When the backend VM is dormant (Paused), the socket is closed or unreachable.",
            "Deploy an intelligent Connection-Buffering Ingress Reverse Proxy (YARP / Envoy / FastMCP Gateway) in front of the VM cluster. The proxy terminates TLS, checks target VM state, holds the client request buffer open if dormant, dispatches a synchronous wake signal (pool_lease / resume) to MXC (<300ms), performs a TCP loopback handshake against guest port :8080 (~50ms), and flushes the held request.",
            "Positive: Clients experience zero connection drops, resets, or 502/504 errors. Standard REST and browser clients work seamlessly without custom wake-up SDKs.",
            "WebSocket & SSE Suspension Multiplexing: Upgrade the JIT Ingress Proxy to support long-lived WebSocket and Server-Sent Events (SSE) connection suspension, enabling real-time UI progress streams and transparent session resumption across mid-conversation idle pauses."
        ),
        (
            "ADR-003: Dedicated Production Base Image Separation",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "The developer golden image (winserv2025-golden.vhdx) includes compilation toolchains (Rust MSVC, Node.js, .NET SDK, Scoop, uv, Playwright, compilers, source repositories). Production deployments require minimized attack surfaces and zero unauthorized tooling.",
            "Maintain a separate, hardened Production Base Image (winserv2025-prod-adpa.vhdx) distinct from the development image. It uses a minimal Windows Server 2025 footprint, pre-bakes ADPA/SIDPA as pre-jitted auto-starting Windows Services under least-privilege local service accounts, excludes all compilers/package managers (Scoop, cargo, git), and runs smoke-test requests during baking to pre-warm memory caches before capturing the golden checkpoint.",
            "Positive: Drastically reduced attack surface, CIS benchmark compliance, and zero JIT compilation latency on wake.",
            "Automated Supply-Chain Attestation (SBOM & Cosign): Integrate automated vulnerability scanning (Trivy), Software Bill of Materials (SBOM) generation, and cryptographic VHDX image signing (Cosign) directly into the CI/CD image baking pipeline so the Hyper-V host verifies image signatures prior to pool registration."
        ),
        (
            "ADR-004: Memory-Preserved Standby (Paused Hypervisor RAM State)",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "Cold-booting Windows Server takes 25–45 seconds. Pausing an active VM keeps guest physical memory intact in host RAM, freezing the virtual CPU instruction pointer.",
            "Implement the warm pool state as Hyper-V Paused Instances. When dormant, VMs remain in Hyper-V Paused state; the host hypervisor stops scheduling vCPU execution ticks (0.0% CPU usage); Dynamic Memory trims and pages unneeded working set memory; resuming via Resume-VM executes in <300ms.",
            "Positive: Sub-300ms wake times with 0.0% idle CPU overhead.",
            "Two-Tier Hibernation Hierarchy (RAM Pause vs. NVMe Save-VM): Introduce a tiered standby hierarchy where hot-queue instances (N=2) remain in Paused RAM state (<300ms wake), while deep-standby instances (N=10) are placed in Saved NVMe state (0MB host RAM, ~1.5s wake) and promoted into RAM dynamically as active leases increase."
        ),
        (
            "ADR-005: Automated Checkpoint Differencing Disks for Stateless Execution",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "If production services write temporary files, logs, or registry entries during an end-user session, those modifications could accumulate over time, leading to disk bloat, performance degradation, or security cross-contamination.",
            "Execute all production sessions against a transient differencing disk (.avhdx) anchored to the clean production baseline. Upon session release or inactivity timeout, the differencing disk is discarded and the VM is reverted to the immutable baseline snapshot. Persistent business data is stored exclusively in external enterprise datastores (SQL Server, PostgreSQL, S3/Blob storage), guaranteeing 100% ephemeral compute.",
            "Positive: Zero post-session state drift and guaranteed eradication of any session residue.",
            "WORM Memory-Backed Ephemeral Scratch Disks: Transition high-throughput temporary scratch I/O from file-backed .avhdx delta layers to Write-Once-Read-Many (WORM) host RAM-disks attached via VMBus SCSI, achieving near-zero I/O latency and instantaneous physical memory zeroing upon release."
        )
    ]

    for title, meta, ctx, dec, cons, fut in adr_items:
        add_h1(doc, title)
        add_body(doc, meta, "Metadata: ")
        add_body(doc, ctx, "Context: ")
        add_body(doc, dec, "Decision & Mechanism: ")
        add_body(doc, cons, "Consequences: ")
        add_callout(doc, fut)
    return doc


def generate_fdd():
    doc = init_doc(
        "Pillar III: Functional Design Document (FDD)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    add_h1(doc, "1. System Architecture & Subsystem Decomposition")
    add_body(doc, "The MXC Production environment decomposes into three tightly coordinated subsystems: (1) The JIT Ingress Proxy Gateway (Buffer Queue, Wake Signal IPC, Health Poller, Session Tracker), (2) The MXC Hardware Lifecycle Controller (Warm Pool Manager, Inactivity Reaper, Differencing Disk Discard), and (3) The Guest Production Appliance (ADPA/SIDPA Windows Service, Health Probe :8080/health, Isolated Virtual NIC, Memory-Resident Working Set).")

    add_h1(doc, "2. Component Specifications")
    add_h2(doc, "2.1 Component 1: JIT Ingress Proxy Gateway")
    add_body(doc, "Reverse Proxy Engine (YARP / Envoy / FastMCP Gateway) running as a system service on the Hyper-V host or DMZ node. Responsibilities include terminating client TLS connections (:443), matching incoming paths to production pool targets (/api/v1/adpa/* -> pool:prod-adpa), maintaining a buffered connection queue while dormant, dispatching wake commands to MXC, proxying HTTP payloads, and resetting session inactivity timers on each packet.")
    add_code_block(doc, """{
  "route_id": "adpa_production_service",
  "match_path": "/api/v1/adpa/{**catch-all}",
  "target_pool": "prod-adpa",
  "guest_port": 8080,
  "wake_timeout_ms": 3000,
  "idle_timeout_seconds": 300,
  "health_check_path": "/health"
}""", "Proxy Route Configuration Schema:")
    add_callout(doc, "Intelligent Circuit-Breaking & Surge Rate-Limiting: Add adaptive token-bucket rate limiting and circuit-breaking at the Ingress Gateway level to protect waking pools from DDoS amplification attacks or thundering-herd webhook storms during traffic spikes.")

    add_h2(doc, "2.2 Component 2: MXC Hardware Lifecycle Controller (wxc-exec)")
    add_body(doc, "Native Rust Hyper-V Backend (src/mxc-sdk/src/backends/hyperv/) with cross-process atomic locking (TransitionLock). Maintains pool state in %ProgramData%\\mxc\\hyperv\\pool\\pool_state.json, executes sub-300ms pool-lease operations via Resume-VM, executes pool-release rollbacks (restoring baseline-hot-ready, deleting .avhdx, and invoking Suspend-VM), and exposes FastMCP/REST telemetry.")
    add_code_block(doc, """stateDiagram-v2
    [*] --> StandbyPaused: Cold Bake & Freeze
    StandbyPaused --> ActiveRunning: Client Request (pool_lease <300ms)
    ActiveRunning --> ActiveRunning: Inbound HTTP Traffic
    ActiveRunning --> ReapingState: Idle Timeout (300s no traffic)
    ReapingState --> RestoreBaseline: Discard .avhdx Delta
    RestoreBaseline --> StandbyPaused: Suspend-VM (CPU: 0%)
    ActiveRunning --> Maintenance: Manual Admin Lock
    Maintenance --> StandbyPaused: Admin Unlock""", "Lifecycle State Machine (Mermaid):")
    add_callout(doc, "Adaptive Idle Timeout Analytics: Replace static 300-second timers with adaptive inactivity thresholds driven by workload telemetry—keeping interactive multi-step workflow sessions warm longer while aggressively reclaiming single-shot webhook instances within 30 seconds.")

    add_h2(doc, "2.3 Component 3: Guest Production Appliance & Image Baking Pipeline (ADPA / SIDPA)")
    add_body(doc, "Runs on Windows Server 2025 Core or Hardened Desktop Experience (winserv2025-prod-adpa.vhdx). Application runs as a self-hosted Windows Service (Kestrel / FastAPI / Go service) on 0.0.0.0:8080. GET /health returns {\"status\": \"healthy\", \"service\": \"ADPA\", \"uptime_ms\": 1240} in <5ms. Assemblies are pre-compiled (Native AOT / NGen) with working set memory warmed prior to capturing baseline-hot-ready. Windows Firewall blocks all inbound traffic except port 8080 from the internal virtual switch and blocks all outbound internet egress.")
    add_callout(doc, "Zero-Downtime Rolling VHDX Updates: Implement a rolling baseline promotion pipeline that registers newly baked production VHDX images into the standby pool alongside active sessions, seamlessly draining older baseline VMs upon idle timeout without dropping a single in-flight client connection.")

    add_h1(doc, "3. Wake-on-Request Sequence & Automated Reaping Protocol")
    add_code_block(doc, """sequenceDiagram
    autonumber
    actor Client as End User / REST Client
    participant Proxy as Ingress Gateway
    participant MXC as MXC Control Plane (wxc-exec)
    participant HyperV as Hypervisor Core
    participant Guest as ADPA Service (Guest :8080)

    Note over HyperV,Guest: State: Paused (0% CPU, Memory Baseline)
    Client->>Proxy: POST /api/v1/adpa/process (Payload: 2MB JSON)
    Proxy->>Proxy: Hold request in memory buffer queue
    Proxy->>MXC: IPC: lease_pool_member("prod-adpa")
    MXC->>HyperV: Resume-VM -VMName "mxc-hv-prod-adpa-01"
    HyperV-->>MXC: Resumed (<300ms)
    MXC-->>Proxy: Leased Sandbox ID: "hv:prod-adpa-01", IP: "172.24.100.5"
    loop Health Probe (Up to 1000ms, typically 50ms)
        Proxy->>Guest: GET http://172.24.100.5:8080/health
        Guest-->>Proxy: HTTP 200 {"status": "healthy"}
    end
    Proxy->>Guest: Forward buffered POST /api/v1/adpa/process
    Guest-->>Proxy: HTTP 200 {"result": "success", "txId": "9482"}
    Proxy-->>Client: HTTP 200 {"result": "success", "txId": "9482"}
    Note over Proxy: Reset idle countdown (300 seconds)""", "Wake-on-Request Execution Sequence:")

    add_body(doc, "When elapsed time since the last packet exceeds idle_timeout_seconds (default: 300s), the Ingress Proxy issues pool_release(\"hv:prod-adpa-01\"). MXC disconnects the network adapter, restores the VM to checkpoint baseline-hot-ready, deletes the child .avhdx differencing disk, invokes Suspend-VM, and marks the instance ready in the pool registry.", "Automated Reaping & Baseline Reset Protocol: ")
    return doc


def generate_user_stories():
    doc = init_doc(
        "Pillar IV: User Stories & Acceptance Criteria",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    stories = [
        (
            "User Story US-01: Low-Latency On-Demand Processing (End User)",
            "As an Enterprise Automation Operator or Upstream REST Client, I want to dispatch requests to the ADPA / SIDPA production endpoints at any time of day, so that my data is processed immediately with sub-second response times without encountering gateway 502/504 errors or waiting for a server cold boot.",
            [
                ("AC-01.1 (Cold Wake TTFB): ", "Given the target Hyper-V VM (hv:prod-adpa-01) is in a dormant (Paused) state, When the client transmits an HTTP POST payload to https://gateway.internal/api/v1/adpa/process, Then the gateway must hold the connection, wake the VM via mxc-pool-lease, and return the initial HTTP response within <= 800ms total wall-clock Time to First Byte (TTFB)."),
                ("AC-01.2 (Subsequent Warm Traffic): ", "Given the VM is already active (Running), When subsequent HTTP requests arrive within the active session window, Then the gateway must forward requests immediately with a proxy overhead of <= 5ms (<= 15ms - 25ms total response overhead) plus application processing time."),
                ("AC-01.3 (Zero Connection Drops & Saturation Fallback): ", "Given normal operating conditions, incoming client requests shall experience zero HTTP 502 Bad Gateway or HTTP 504 Gateway Timeout errors due to VM wake-up latency. Given an extreme host saturation event where wake-up exceeds wake_timeout_ms (3000ms), the gateway must gracefully return a structured HTTP 503 Service Unavailable with a Retry-After header rather than dropping the TCP socket.")
            ],
            "Interactive SSE Wake-Up Telemetry: Provide an optional client-side loading skeleton or progress stream via Server-Sent Events (SSE) for browser portals so end users receive immediate visual confirmation ('Resuming isolated secure enclave...') within 10ms of connection hold."
        ),
        (
            "User Story US-02: Cryptographic State Rollback & Zero Persistence (SecOps)",
            "As a Chief Information Security Officer (CISO) and Compliance Auditor, I want every execution session of SIDPA to run inside a hardware-isolated environment that is mathematically wiped clean upon completion, so that malicious payloads, memory scrapers, or sensitive customer records cannot persist across different user sessions.",
            [
                ("AC-02.1 (Ephemeral Differencing Disks): ", "Given an active processing session where files, temporary tables, or registry keys were modified in the guest, When the session ends or the 300-second inactivity timer expires, Then the Differencing Delta Disk (.avhdx) must be permanently deleted from host storage, leaving zero residual files or logs."),
                ("AC-02.2 (Cryptographic Baseline Verification): ", "Given a completed session rollback, When the VM is reverted to the baseline-hot-ready checkpoint, Then SHA-256 verification of the parent base VHDX (winserv2025-prod-adpa.vhdx) must remain bit-for-bit identical before and after execution."),
                ("AC-02.3 (Network Airgap Default): ", "Given a production guest instance, When the instance is active or dormant, Then its virtual network adapter must be strictly disconnected from external internet switches (mxc-net-disable) and restricted exclusively to the internal gateway virtual switch (:8080).")
            ],
            "Zero-Fill Scrubbing & Per-Session Key Rotation: Integrate automated zero-fill block scrubbing passes and ephemeral per-session BitLocker/virtual-TPM key rotation so that discarded .avhdx sectors leave zero physical data remanence on host NVMe arrays."
        ),
        (
            "User Story US-03: High-Density Scale-to-Zero Virtualization (DevOps & SRE)",
            "As an Infrastructure Platform Engineer, I want dormant production instances to release active CPU and compress RAM usage, so that our on-premise Windows Server / Hyper-V cluster can host 5x to 10x more application workloads than traditional always-on VMs.",
            [
                ("AC-03.1 (Zero CPU Utilization): ", "Given 10 registered production service VMs in the warm standby pool, When no client requests are active (Paused state), Then total host CPU utilization across all 10 VMs must measure strictly 0.0% on the Hyper-V host performance monitor."),
                ("AC-03.2 (Dynamic Memory Compression): ", "Given suspended standby instances, When Hyper-V Dynamic Memory is active, Then the host hypervisor must reclaim unallocated guest RAM and compress idle memory commitment down to the configured minimum baseline (>= 65% reduction)."),
                ("AC-03.3 (Sub-300ms Hypervisor Wakeup & Pool Queue): ", "Given a configurable ready queue size (N), When the Ingress Gateway dispatches a wake signal, Then the elapsed time for Hyper-V to complete Resume-VM must be <= 300ms.")
            ],
            "Automated NUMA Node Alignment: Implement host-level Non-Uniform Memory Access (NUMA) node pinning and intelligent memory overcommit policies in wxc-exec, maximizing physical server tenant density by up to 300% without cross-socket memory latency degradation."
        ),
        (
            "User Story US-04: Automated Release Image Baking (CI/CD Pipeline)",
            "As a Software Release Engineer, I want an automated host-driven pipeline to bake production-ready application releases into a clean base VHDX, so that production images are consistent, pre-jitted, and guaranteed free of development debris.",
            [
                ("AC-04.1 (Clean Image Specification): ", "Given a newly built production base VHDX (winserv2025-prod-adpa.vhdx), When inspected by the release audit script, Then it must contain only the compiled application binary, required Windows runtime dependencies, and hardened security profiles—with all compilers, package managers (Scoop, uv, cargo), and source code repositories completely absent."),
                ("AC-04.2 (Automated Pre-Warming): ", "Given the automated image baking script, When provisioning completes, Then the script must start the ADPA/SIDPA Windows Service, execute a synthetic health-check request against localhost:8080/health, verify database connectivity, and capture the baseline-hot-ready checkpoint while the application working set is hot in RAM.")
            ],
            "Canary Baseline Verification & Auto-Rollback: Extend the CI/CD baking pipeline to automatically route 5% of live ingress traffic to the newly baked VHDX baseline for a 15-minute canary window, automatically reverting the pool pointer to the previous baseline checkpoint if error rates or latency thresholds deviate."
        )
    ]

    for title, narrative, ac_list, fut in stories:
        add_h1(doc, title)
        add_body(doc, narrative, "Story Narrative: ")
        add_h2(doc, "Acceptance Criteria (BDD / Gherkin)")
        for prefix, ac_text in ac_list:
            add_body(doc, ac_text, prefix)
        add_callout(doc, fut)
    return doc


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target Output Directory: {OUTPUT_DIR}")

    tasks = [
        ("ARCHITECTURE_DESIGN_DOCUMENT-v2.docx", generate_master_add),
        ("ARCHITECTURE_DESIGN_DOCUMENT_Merged.docx", generate_master_add),
        ("BDR_Enterprise_Architecture-v2.docx", generate_bdr),
        ("ADR_Enterprise_Architecture-v2.docx", generate_adr),
        ("FDD_Enterprise_Architecture-v2.docx", generate_fdd),
        ("UserStories_Enterprise_Architecture-v2.docx", generate_user_stories),
    ]

    for filename, generator in tasks:
        filepath = OUTPUT_DIR / filename
        doc = generator()
        doc.save(str(filepath))
        size_kb = filepath.stat().st_size / 1024
        print(f"  [+] Generated: {filepath.name} ({size_kb:.1f} KB)")

    print(f"\nSuccessfully generated all {len(tasks)} Word (.docx) documents in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
