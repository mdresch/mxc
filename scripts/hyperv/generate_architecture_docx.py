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


def build_add_content(doc):
    add_h1(doc, "1. Executive Summary")
    add_body(doc, "This Architecture Design Document (ADD) defines the unified enterprise specification for running production-grade services—specifically ADPA (Automated Dynamic Process Automation) and SIDPA (Secured Intelligent Data Processing Application)—inside hardware-isolated Windows Server 2025 Type-1 Hyper-V micro-instances.")
    add_body(doc, "When no client requests are active, production VMs remain suspended in RAM (Paused), consuming 0.0% CPU cycles with a lean, pre-trimmed static working set (~1.0–1.2 GB).", "• 0% Idle Resource Footprint: ")
    add_body(doc, "An intelligent Ingress Gateway buffers incoming client HTTP requests, triggers hardware unpause via the MXC control plane in <300ms, verifies socket readiness, and proxies the payload with zero perceptible cold-start delay (350ms – 650ms nominal, <= 800ms SLA Time to First Byte).", "• Sub-Second Wake-on-Request: ")
    add_body(doc, "Upon session completion or inactivity timeout, the instance delta disk (.avhdx) is discarded, returning the VM back to a pristine, immutable checkpoint baseline (baseline-hot-ready) to prevent state drift and eliminate malware persistence.", "• Sterile Session Isolation: ")
    add_body(doc, "As soon as requirements, concurrency velocity, or schedules signal increased demand, the warm pool manager automatically replenishes and expands the ready-state paused buffer (Kmin -> Kmax) so concurrent requests never experience cold boots or queuing delays.", "• Elastic Ready-State Autoscaling: ")

    add_h1(doc, "2. Pillar Index")
    add_body(doc, "Business context, ROI drivers, cost metrics, high-level requirements matrix (REQ-BDR-01 to 05), and zero-trust security requirements.", "• Pillar I — Business Drivers & Requirements (BDR): ")
    add_body(doc, "Formal decision records (ADR-001 through ADR-006) justifying Hyper-V Type-1 virtualization, JIT wake-on-request proxies, separate production images, paused RAM standby states, differencing disk rollback, and dynamic watermark pool autoscaling.", "• Pillar II — Architectural Decision Records (ADR): ")
    add_body(doc, "Component breakdown, JSON proxy route configuration, elastic watermark pool replenishment algorithm, lifecycle state machines, wake-on-request sequence flows, and automated reaping protocols.", "• Pillar III — Functional Design Document (FDD): ")
    add_body(doc, "BDD/Gherkin user stories and testable acceptance criteria across End Users (US-01), SecOps (US-02), DevOps/SRE (US-03), CI/CD Release Engineers (US-04), and Capacity SREs (US-05).", "• Pillar IV — User Stories & Acceptance Criteria: ")

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
    Reaper -- "Inactivity timeout" --> PoolManager -- "Discard .avhdx & Restore" --> StandbyVM""")

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


def generate_master_add():
    doc = init_doc(
        "Architecture Design Document (ADD)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes for Enterprise Applications (ADPA / SIDPA)"
    )
    build_add_content(doc)
    return doc


def build_bdr_content(doc):
    add_h1(doc, "1. Executive Context & Operational Trilemma")
    add_body(doc, "Enterprises deploying automated processing services (such as ADPA and SIDPA) face a critical operational trilemma across cost, latency, and security:")
    add_body(doc, "Traditional deployments maintain dedicated, always-on virtual machines to avoid slow startup times. A cluster of 10–20 always-on Windows Server instances consumes significant host CPU ticks, saturates hypervisor RAM, and incurs 24/7 compute and licensing costs even during idle nights and weekends.", "1. High Infrastructure & Idle Power Costs: ")
    add_body(doc, "When traditional virtual machines are shut down (Stopped) to save resources, waking them upon an incoming HTTP request takes 25 to 45 seconds, leading to HTTP 504 gateway timeouts and failed webhooks.", "2. Unacceptable Cold-Boot Delays: ")
    add_body(doc, "While Linux containers achieve fast spin-up, they share the host kernel. High-compliance workloads processing confidential financial data, PII, or proprietary AI weights require a true Type-1 Hypervisor hardware boundary (Hyper-V Ring-0 isolation).", "3. Inadequate Security in Shared Container Runtimes: ")

    add_h1(doc, "2. Core Business Drivers (Strategic Goals)")
    add_h2(doc, "BDR-01: Maximum Resource Density & Cost Reduction (Scale-to-Zero)")
    add_body(doc, "Minimize hardware footprint and operating expenditure by ensuring that when zero client requests are pending, virtual machine instances consume 0% CPU and maintain a compact host memory footprint.", "Goal: ")
    add_body(doc, "0.0% Host CPU consumption during idle periods; ~1.0–1.2 GB lean static host memory footprint per paused instance achieved via working set pre-trimming prior to snapshot capture (preventing host swap-in disk I/O on resume); support for 3x to 5x more concurrent registered services per physical host.", "Target Metrics: ")
    add_callout(doc, "Predictive Auto-Warming & Same-Page Merging: Introduce machine learning ingress forecasting models that analyze historical tenant traffic patterns to proactively resume anticipated pools 5 seconds before traffic surges occur, paired with hypervisor memory deduplication (Kernel Same-Page Merging) and Carbon-Aware scheduling across green data centers.")

    add_h2(doc, "BDR-02: Strict Sub-Second Response SLAs (Instantaneous Readiness)")
    add_body(doc, "Provide instantaneous, consumer-grade responsiveness to end users and API integrations without manual provisioning.", "Goal: ")
    add_body(doc, "Time to First Byte (TTFB) from a completely dormant/paused state of 350ms – 650ms (<= 800ms SLA); subsequent warm request latency under 15ms.", "Target Metrics: ")
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
            ["REQ-BDR-01", "Performance", "Ingress gateway must buffer incoming requests and wake dormant VM in <300ms (350ms - 650ms nominal, <= 800ms total TTFB SLA).", "Measured gateway latency logs <= 300ms to VM resume and socket connect."],
            ["REQ-BDR-02", "Lifecycle", "Instances with no traffic for >300s must automatically revert to baseline and suspend.", "Verified automated snapshot rollback and Hyper-V Paused state transition."],
            ["REQ-BDR-03", "Security", "Guest application traffic restricted to Ingress Gateway port forwarding (:8080) and strict enterprise datastore and infrastructure egress whitelist (SQL, PostgreSQL, S3 private endpoints, Internal DNS, Kerberos); arbitrary public internet egress blocked.", "Network firewall rules strictly enforce isolation; no unauthorized internet egress."],
            ["REQ-BDR-04", "Packaging", "Production image must exclude developer toolchains, debuggers, and source repositories.", "Verified clean golden base image (winserv2025-prod-adpa.vhdx) containing only pre-jitted production binaries and hardened OS."],
            ["REQ-BDR-05", "Elasticity", "As soon as demand indicators surge or a standby instance is leased, the pool must automatically unpause/replenish ready instances up to Kmax.", "Verified standby pool depth auto-replenishment with zero queuing drops under concurrent load."]
        ]
    )


def generate_bdr():
    doc = init_doc(
        "Pillar I: Business Drivers & Requirements (BDR)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    build_bdr_content(doc)
    return doc


def build_adr_content(doc):
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
            "Implement the warm pool state as Hyper-V Paused Instances. When dormant, VMs remain in Hyper-V Paused state with instruction pointers frozen (0.0% CPU). Rather than relying on the guest balloon driver to actively reclaim memory while its vCPUs are frozen (which is impossible when paused) or forcing host swap-paging (which violates the <300ms resume SLA due to disk I/O page-ins), guest memory is aggressively trimmed and compacted prior to issuing Suspend-VM during pool replenishment and image baking. This locks each dormant instance into a lean static host RAM allocation (~1.0–1.2 GB). Resuming via Resume-VM executes in <300ms.",
            "Positive: Guaranteed deterministic sub-300ms wake times with 0.0% idle CPU overhead. Trade-off: Requires sizing host physical RAM to accommodate K_ready warm paused instances without triggering host-level memory overcommit swap.",
            "Two-Tier Hibernation Hierarchy (RAM Pause vs. NVMe Save-VM): Introduce a tiered standby hierarchy where hot-queue instances (N=2) remain in Paused RAM state (<300ms wake), while deep-standby instances (N=10) are placed in Saved NVMe state (0MB host RAM, ~1.5s wake) and promoted into RAM dynamically as active leases increase."
        ),
        (
            "ADR-005: Automated Checkpoint Differencing Disks for Stateless Execution",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "If production services write temporary files, logs, or registry entries during an end-user session, those modifications could accumulate over time, leading to disk bloat, performance degradation, or security cross-contamination.",
            "Execute all production sessions against a transient differencing disk (.avhdx) anchored to the clean production baseline (baseline-hot-ready). All disk writes during the session are captured exclusively in the .avhdx layer and discarded upon session release. Persistent business data is stored exclusively in external enterprise datastores via an Internal Data Plane & Egress Whitelist: public internet egress is strictly blocked (airgap default), while outbound traffic is permitted strictly to internal datastore subnets (TCP 1433 for SQL Server, TCP 5432 for PostgreSQL, TCP 443 for Private S3/Blob storage) and directory services (UDP/TCP 53 for Internal DNS, UDP/TCP 88 for Active Directory Kerberos).",
            "Positive: Zero post-session state drift, guaranteed eradication of session residue, and secure persistence to external datastores without exposing internet access.",
            "WORM Memory-Backed Ephemeral Scratch Disks: Transition high-throughput temporary scratch I/O from file-backed .avhdx delta layers to Write-Once-Read-Many (WORM) host RAM-disks attached via VMBus SCSI, achieving near-zero I/O latency and instantaneous physical memory zeroing upon release."
        ),
        (
            "ADR-006: Dynamic Watermark-Based Standby Pool Autoscaling & Predictive Warm-Up",
            "Accepted | Date: October 2026 | Deciders: Systems Architecture Team",
            "While maintaining a single dormant instance in Paused RAM achieves sub-300ms wake-up for a single request, a burst of concurrent requests or high-volume batch processing for ADPA/SIDPA could exhaust the standby capacity. Production systems require elastic, proactive ready-state replenishment so multiple warm instances are immediately available whenever demand indicators surge.",
            "Implement an Adaptive Low/High Watermark Standby Pool Manager with tiered lifecycle states: (1) ColdProvisioned (0MB RAM, disk provisioned on NVMe), (2) StandbyPaused (pre-warmed, pre-trimmed, paused in RAM at ~1.0–1.2 GB, <300ms wake), and (3) ActiveRunning. Low Watermark Kmin maintains ready instances; when an instance is leased, an async background worker promotes a ColdProvisioned VM in ~1.5s. High Watermark Kmax dynamically expands the buffer under surge velocity. Sibling VM PRNG entropy is re-seeded from hardware (RDRAND/BCryptGenRandom) on wake, stale database connection pools are cleared (ClearAllPools()), and guest clock sync against host UTC time is asserted on resume before serving requests.",
            "Positive: Seamless concurrency handling with zero queuing delay; zero cold boots; cryptographic security against PRNG entropy duplication; zero clock-skew authentication errors. Trade-off: Burst expansion momentarily consumes additional host RAM (~1.0–1.2 GB per paused instance), reclaimed back to disk upon idle cooldown.",
            "AI-Driven Predictive Ingress Forecasting: Train an on-host lightweight time-series model (e.g., ARIMA or temporal transformer) analyzing historical request telemetry to automatically pre-warm pools 60 seconds ahead of anticipated demand cycles with zero manual scheduling."
        )
    ]

    for title, meta, ctx, dec, cons, fut in adr_items:
        add_h1(doc, title)
        add_body(doc, meta, "Metadata: ")
        add_body(doc, ctx, "Context: ")
        add_body(doc, dec, "Decision & Mechanism: ")
        add_body(doc, cons, "Consequences: ")
        add_callout(doc, fut)


def generate_adr():
    doc = init_doc(
        "Pillar II: Architectural Decision Records (ADR)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    build_adr_content(doc)
    return doc


def build_fdd_content(doc):
    add_h1(doc, "1. System Architecture & Subsystem Decomposition")
    add_body(doc, "The MXC Production environment decomposes into three tightly coordinated subsystems: (1) The JIT Ingress Proxy Gateway (Buffer Queue, Wake Signal IPC, In-Flight Request Tracker, Health/Clock Poller), (2) The MXC Hardware Lifecycle Controller (Warm Pool Manager, Inactivity Reaper, Differencing Disk Discard, TransitionLock), and (3) The Guest Production Appliance (ADPA/SIDPA Windows Service, Health Probe :8080/health, Internal Egress Whitelist, Memory-Resident Working Set).")

    add_h1(doc, "2. Component Specifications")
    add_h2(doc, "2.1 Component 1: JIT Ingress Proxy Gateway")
    add_body(doc, "Reverse Proxy Engine (YARP / Envoy / FastMCP Gateway) running as a system service on the Hyper-V host or DMZ node. Responsibilities include terminating client TLS connections (:443), matching incoming paths to production pool targets (/api/v1/adpa/* -> pool:prod-adpa), maintaining a buffered connection queue while dormant, dispatching wake commands to MXC, proxying HTTP payloads, maintaining an atomic active_open_requests counter, enforcing a hard max_request_execution_timeout_seconds (default 900s) to prevent hung requests from permanently blocking reaping, and executing atomic TransitionLock reaping to prevent race conditions.")
    add_code_block(doc, """{
  "route_id": "adpa_production_service",
  "match_path": "/api/v1/adpa/{**catch-all}",
  "target_pool": "prod-adpa",
  "guest_port": 8080,
  "wake_timeout_ms": 3000,
  "idle_timeout_seconds": 300,
  "max_request_execution_timeout_seconds": 900,
  "health_check_path": "/health"
}""", "Proxy Route Configuration Schema:")
    add_callout(doc, "Intelligent Circuit-Breaking & Surge Rate-Limiting: Add adaptive token-bucket rate limiting and circuit-breaking at the Ingress Gateway level to protect waking pools from DDoS amplification attacks or thundering-herd webhook storms during traffic spikes.")

    add_h2(doc, "2.2 Component 2: MXC Hardware Lifecycle Controller (wxc-exec)")
    add_body(doc, "Native Rust Hyper-V Backend (src/mxc-sdk/src/backends/hyperv/) with cross-process atomic locking (TransitionLock). Maintains pool state in %ProgramData%\\mxc\\hyperv\\pool\\pool_state.json, executes sub-300ms pool-lease operations via Resume-VM, executes pool-release rollbacks (restoring baseline-hot-ready, deleting .avhdx, and invoking Suspend-VM), and exposes FastMCP/REST telemetry.")
    add_code_block(doc, """stateDiagram-v2
    [*] --> ColdProvisioned: Differencing Disk Attached (0MB Host RAM)
    ColdProvisioned --> StandbyPaused: Background Pre-Warm & Suspend-VM (~1.5s, 1GB RAM, 0% CPU)
    StandbyPaused --> ActiveRunning: Client Request (pool_lease <300ms)
    ActiveRunning --> ActiveRunning: Inbound HTTP Traffic (active_open_requests > 0)
    ActiveRunning --> ReapingState: Idle Timeout (active_open_requests == 0 & t > 300s)
    ReapingState --> StandbyPaused: Discard .avhdx & Restore Baseline (if pool count <= Kmax)
    ReapingState --> ColdProvisioned: Reclaim Host RAM / Stop-VM (if surplus beyond Kmin)
    ActiveRunning --> Maintenance: Manual Admin Lock
    Maintenance --> StandbyPaused: Admin Unlock""", "Lifecycle State Machine (Mermaid):")
    add_body(doc, "Low Watermark Enforcement (Kmin >= 1): The controller maintains ready-state standby instances. When an instance is leased, an async background worker immediately unpauses/promotes a ColdProvisioned VM in ~1.5s. High Watermark Surge Autoscaling (Kmax up to 5-10): Velocity and queue triggers dynamically expand the buffer to absorb burst traffic with zero cold boots.", "• Elastic Standby Replenishment & Autoscaler: ")
    add_code_block(doc, """{
  "pool_id": "prod-adpa",
  "min_ready_standby": 1,
  "max_ready_standby": 5,
  "surge_velocity_threshold_rps": 10,
  "queue_depth_trigger": 1,
  "idle_timeout_seconds": 300,
  "reaping_cooldown_seconds": 180,
  "pre_warm_schedule": [
    { "cron": "0 8 * * 1-5", "target_ready": 4, "duration_minutes": 60 }
  ]
}""", "Pool Configuration Schema (pool_config.json):")
    add_callout(doc, "Adaptive Idle Timeout Analytics: Replace static 300-second timers with adaptive inactivity thresholds driven by workload telemetry—keeping interactive multi-step workflow sessions warm longer while aggressively reclaiming single-shot webhook instances within 30 seconds.")

    add_h2(doc, "2.3 Component 3: Guest Production Appliance & Image Baking Pipeline (ADPA / SIDPA)")
    add_body(doc, "Runs on Windows Server 2025 Core or Hardened Desktop Experience (winserv2025-prod-adpa.vhdx). Application runs as a self-hosted Windows Service (Kestrel / FastAPI / Go service) on 0.0.0.0:8080. GET /health verifies service health, asserts Hyper-V clock synchronization (abs(GuestTime - HostTime) < 50ms) to prevent TLS/Kerberos clock skew, re-seeds hardware PRNG entropy (RDRAND/BCryptGenRandom), and flushes stale connection pools (ClearAllPools()). Outbound traffic is restricted via an Internal Data Plane Whitelist (TCP 1433 for SQL Server, TCP 5432 for PostgreSQL, TCP 443 for S3 Private Endpoints, UDP/TCP 53 for Internal DNS, and UDP/TCP 88 for Kerberos) with arbitrary public internet egress blocked.")
    add_callout(doc, "Zero-Downtime Rolling VHDX Updates: Implement a rolling baseline promotion pipeline that registers newly baked production VHDX images into the standby pool alongside active sessions, seamlessly draining older baseline VMs upon idle timeout without dropping a single in-flight client connection.")

    add_h1(doc, "3. Wake-on-Request Sequence & Automated Reaping Protocol")
    add_code_block(doc, """sequenceDiagram
    autonumber
    actor Client as End User / REST Client
    participant Proxy as Ingress Gateway
    participant MXC as MXC Control Plane (wxc-exec)
    participant HyperV as Hypervisor Core
    participant Guest as ADPA Service (Guest :8080)
    participant DB as Internal Enterprise Datastore

    Note over HyperV,Guest: State: StandbyPaused (0% CPU, Memory Resident)
    Client->>Proxy: POST /api/v1/adpa/process (Payload: 2MB JSON)
    Proxy->>Proxy: Hold request in memory buffer queue
    Proxy->>MXC: IPC: lease_pool_member("prod-adpa")
    MXC->>HyperV: Resume-VM -VMName "mxc-hv-prod-adpa-01"
    HyperV-->>MXC: Resumed (<300ms)
    MXC-->>Proxy: Leased Sandbox ID: "hv:prod-adpa-01", IP: "172.24.100.5"
    loop Health, PRNG & DB Pool Probe (Up to 1000ms, typically 50ms)
        Proxy->>Guest: GET http://172.24.100.5:8080/health
        Guest->>Guest: Re-seed PRNG (RDRAND), Clear DB Pools (ClearAllPools), Assert Host Clock Sync
        Guest-->>Proxy: HTTP 200 {"status": "healthy", "clock_synced": true}
    end
    Proxy->>Guest: Forward buffered POST (Increment active_open_requests)
    Guest->>DB: TCP 1433/5432/443: Query & Write Results via Egress Whitelist
    DB-->>Guest: Transaction OK
    Guest-->>Proxy: HTTP 200 {"result": "success", "txId": "9482"} (Decrement active_open_requests)
    Proxy-->>Client: HTTP 200 {"result": "success", "txId": "9482"}
    Note over Proxy: If active_open_requests == 0, reset idle countdown (300 seconds)""", "Wake-on-Request Execution Sequence:")

    add_body(doc, "When active_open_requests == 0 and elapsed time exceeds idle_timeout_seconds (300s), the Ingress Proxy acquires an atomic TransitionLock marking the VM Reaping in the routing table (eliminating race conditions). It then issues pool_release: MXC disconnects network adapters, restores baseline-hot-ready, discards the child .avhdx disk, invokes Suspend-VM, and updates pool_state.json.", "Automated Reaping & Baseline Reset Protocol: ")


def generate_fdd():
    doc = init_doc(
        "Pillar III: Functional Design Document (FDD)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    build_fdd_content(doc)
    return doc


def build_user_stories_content(doc):
    stories = [
        (
            "User Story US-01: Low-Latency On-Demand Processing (End User)",
            "As an Enterprise Automation Operator or Upstream REST Client, I want to dispatch requests to the ADPA / SIDPA production endpoints at any time of day, so that my data is processed immediately with sub-second response times without encountering gateway 502/504 errors or waiting for a server cold boot.",
            [
                ("AC-01.1 (Cold Wake TTFB & Platform Overhead): ", "Given the target Hyper-V VM (hv:prod-adpa-01) is in a dormant (Paused) state, When the client transmits an HTTP POST payload to https://gateway.internal/api/v1/adpa/process, Then the gateway must hold the connection, wake the VM via mxc-pool-lease (<= 300ms platform wake overhead), establish the socket connection, and return the initial HTTP response/header flush within <= 800ms total wall-clock Time to First Byte (TTFB), before streaming subsequent business logic payloads."),
                ("AC-01.2 (Subsequent Warm Traffic): ", "Given the VM is already active (Running), When subsequent HTTP requests arrive within the active session window, Then the gateway must forward requests immediately with a proxy overhead of <= 5ms (<= 15ms - 25ms total response overhead) plus application processing time."),
                ("AC-01.3 (Zero Connection Drops & Saturation Fallback): ", "Given normal operating conditions, incoming client requests shall experience zero HTTP 502 Bad Gateway or HTTP 504 Gateway Timeout errors due to VM wake-up latency. Given an extreme host saturation event where wake-up exceeds wake_timeout_ms (3000ms), the gateway must gracefully return a structured HTTP 503 Service Unavailable with a Retry-After header rather than dropping the TCP socket.")
            ],
            "Interactive SSE Wake-Up Telemetry: Provide an optional client-side loading skeleton or progress stream via Server-Sent Events (SSE) for browser portals so end users receive immediate visual confirmation ('Resuming isolated secure enclave...') within 10ms of connection hold."
        ),
        (
            "User Story US-02: Cryptographic State Rollback & Zero Persistence (SecOps)",
            "As a Chief Information Security Officer (CISO) and Compliance Auditor, I want every execution session of SIDPA to run inside a hardware-isolated environment that is mathematically wiped clean upon completion, so that malicious payloads, memory scrapers, or sensitive customer records cannot persist across different user sessions.",
            [
                ("AC-02.1 (Ephemeral Differencing Disks & Safety Timeout): ", "Given an active processing session where files, temporary tables, or registry keys were modified in the guest, When the session ends or the 300-second inactivity timer expires (with active_open_requests == 0), Then the Differencing Delta Disk (.avhdx) must be permanently deleted from host storage, leaving zero residual files or logs; and if any request hangs beyond max_request_execution_timeout_seconds (900s), the gateway terminates it with HTTP 504, decrements the counter, and initiates reaping."),
                ("AC-02.2 (Cryptographic Baseline Verification): ", "Given a completed session rollback, When the VM is reverted to the baseline-hot-ready checkpoint, Then SHA-256 verification of the parent base VHDX (winserv2025-prod-adpa.vhdx) must remain bit-for-bit identical before and after execution."),
                ("AC-02.3 (Network Airgap & Datastore/Directory Egress Whitelist): ", "Given a production guest instance, When the instance is active or dormant, Then arbitrary public internet egress must be strictly blocked (airgap mode), And outbound traffic is restricted exclusively to internal enterprise infrastructure and datastores: TCP 1433 for SQL Server, TCP 5432 for PostgreSQL, TCP 443 for S3/Blob storage private endpoints, UDP/TCP 53 for Internal DNS, and UDP/TCP 88 for Active Directory Kerberos."),
                ("AC-02.4 (PRNG Hardware Entropy, DB Pool Flush & Clock Sync): ", "Given a VM restored from baseline-hot-ready memory checkpoint, When the guest service initializes upon wake, Then it must forcibly re-seed its random number generator from CPU hardware (RDRAND / BCryptGenRandom) to guarantee unique cryptographic nonces and UUIDs across sibling cloned VMs, flush and clear active database driver connection pools (ClearAllPools()) to prevent TCP connection resets caused by dead pooled sockets held across checkpoint sleep, And verify clock synchronization against host UTC time before returning HTTP 200 on the health probe.")
            ],
            "Zero-Fill Scrubbing & Per-Session Key Rotation: Integrate automated zero-fill block scrubbing passes and ephemeral per-session BitLocker/virtual-TPM key rotation so that discarded .avhdx sectors leave zero physical data remanence on host NVMe arrays."
        ),
        (
            "User Story US-03: High-Density Scale-to-Zero Virtualization (DevOps & SRE)",
            "As an Infrastructure Platform Engineer, I want dormant production instances to release active CPU and compress RAM usage, so that our on-premise Windows Server / Hyper-V cluster can host 5x to 10x more application workloads than traditional always-on VMs.",
            [
                ("AC-03.1 (Zero CPU Utilization): ", "Given 10 registered production service VMs in the warm standby pool, When no client requests are active (Paused state), Then total host CPU utilization across all 10 VMs must measure strictly 0.0% on the Hyper-V host performance monitor."),
                ("AC-03.2 (Lean Static Host Memory Footprint): ", "Given suspended standby instances in StandbyPaused state, When measured on the host hypervisor, Then each dormant VM's host RAM commitment must not exceed ~1.0–1.2 GB (achieved via working set pre-trimming prior to snapshot capture), eliminating host swap-in disk page latency on resume."),
                ("AC-03.3 (Sub-300ms Hypervisor Wakeup & Pool Queue): ", "Given a configurable ready queue size (N), When the Ingress Gateway dispatches a wake signal, Then the elapsed time for Hyper-V to complete Resume-VM must be <= 300ms.")
            ],
            "Automated NUMA Node Alignment: Implement host-level Non-Uniform Memory Access (NUMA) node pinning and intelligent memory overcommit policies in wxc-exec, maximizing physical server tenant density by up to 300% without cross-socket memory latency degradation."
        ),
        (
            "User Story US-04: Automated Release Image Baking (CI/CD Pipeline)",
            "As a Software Release Engineer, I want an automated host-driven pipeline to bake production-ready application releases into a clean base VHDX, so that production images are consistent, pre-jitted, and guaranteed free of development debris.",
            [
                ("AC-04.1 (Clean Image Specification): ", "Given a newly built production base VHDX (winserv2025-prod-adpa.vhdx), When inspected by the release audit script, Then it must contain only the compiled application binary, required Windows runtime dependencies, and hardened security profiles—with all compilers, package managers (Scoop, uv, cargo), and source code repositories completely absent."),
                ("AC-04.2 (Automated Pre-Warming & Connection Pool Hygiene): ", "Given the automated image baking script, When provisioning completes, Then the script must start the ADPA/SIDPA Windows Service, execute a synthetic health-check request against localhost:8080/health, verify database connectivity, explicitly close all open database connection handles / clear connection pools to prevent persisting stale TCP sockets in RAM, and capture the baseline-hot-ready checkpoint while the application working set is hot in memory.")
            ],
            "Canary Baseline Verification & Auto-Rollback: Extend the CI/CD baking pipeline to automatically route 5% of live ingress traffic to the newly baked VHDX baseline for a 15-minute canary window, automatically reverting the pool pointer to the previous baseline checkpoint if error rates or latency thresholds deviate."
        ),
        (
            "User Story US-05: Elastic Standby Capacity & Concurrency Burst Scaling (DevOps & SRE)",
            "As an SRE and Capacity Planning Engineer, I want the warm pool manager to automatically replenish and expand the ready-state paused instances as soon as demand indicators increase, so that concurrent client requests and unexpected traffic surges always find a pre-warmed instance immediately available with zero queuing delays.",
            [
                ("AC-05.1 (Instant Buffer Replenishment): ", "Given a configured minimum standby buffer (Kmin = 1), When an incoming request leases the active standby VM (hv:prod-adpa-01), Then the pool manager must immediately dispatch an asynchronous worker to promote a ColdProvisioned instance into StandbyPaused state in ~1.5s in the background before the next request arrives."),
                ("AC-05.2 (Velocity-Triggered Dynamic Expansion): ", "Given incoming request velocity exceeds the configured threshold (> 10 req/s) or Ingress Buffer queue depth > 0, When the autoscaling trigger evaluates, Then the pool manager must dynamically scale the ready-state buffer up to Kmax (up to 5 instances in RAM), ensuring concurrent requests are served without cold-boot penalties."),
                ("AC-05.3 (Schedule & Requirement-Based Pre-Warming): ", "Given scheduled batch processing or calendar events (e.g., 08:00 AM shift start), When an automated or manual pre-warm signal (POST /pool/warm --target prod-adpa --count 4) is received, Then the pool manager must pre-warm the requested ready instances in StandbyPaused state prior to traffic arrival."),
                ("AC-05.4 (Graceful Scale-Down & Memory Reclamation): ", "Given traffic has normalized and surplus burst instances have remained idle past reaping_cooldown_seconds (180s), When the reaper evaluates the fleet, Then surplus instances beyond Kmin must be systematically restored to baseline, differencing disks discarded, and VMs suspended or deallocated to ColdProvisioned to return host RAM to baseline.")
            ],
            "Cross-Host Predictive Pool Rebalancing: Coordinate with multi-node hypervisor schedulers to dynamically distribute ready-state buffers across secondary physical Hyper-V nodes when local host memory pressure exceeds 80%."
        )
    ]

    for title, narrative, ac_list, fut in stories:
        add_h1(doc, title)
        add_body(doc, narrative, "Story Narrative: ")
        add_h2(doc, "Acceptance Criteria (BDD / Gherkin)")
        for prefix, ac_text in ac_list:
            add_body(doc, ac_text, prefix)
        add_callout(doc, fut)


def generate_user_stories():
    doc = init_doc(
        "Pillar IV: User Stories & Acceptance Criteria",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)"
    )
    build_user_stories_content(doc)
    return doc


def generate_merged_master_document():
    doc = init_doc(
        "Enterprise Architecture Specification (Complete Merged Edition)",
        "Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA) — Master ADD & Pillars I–IV"
    )

    # Master ADD
    build_add_content(doc)

    # Pillar I: BDR
    doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run("Pillar I: Business Drivers & Requirements (BDR)")
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)
    build_bdr_content(doc)

    # Pillar II: ADR
    doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run("Pillar II: Architectural Decision Records (ADR)")
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)
    build_adr_content(doc)

    # Pillar III: FDD
    doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run("Pillar III: Functional Design Document (FDD)")
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)
    build_fdd_content(doc)

    # Pillar IV: User Stories
    doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run("Pillar IV: User Stories & Acceptance Criteria")
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)
    build_user_stories_content(doc)

    return doc


def build_lessons_learned_content(doc):
    add_h1(doc, "1. Executive Summary & Context")
    add_body(
        doc,
        "The MXC Hyper-V JIT Scale-to-Zero project engineered a production execution platform capable of running full-isolation Windows Server workloads on bare-metal Type-1 hypervisors with zero idle compute cost and sub-300ms wake-on-request latency. This document captures the low-level hypervisor, storage, and concurrency lessons learned across all engineering phases."
    )

    add_h1(doc, "2. Hypervisor Control Plane & RPC Deadlocks")
    add_h2(doc, "2.1 Unbounded Filesystem Traversal vs. VMBus Contention")
    add_body(doc, "Early automation scripts utilizing unbounded recursive traversal (e.g., Get-ChildItem -Recurse) caused host freezes, VS Code extension host RPC timeouts, and Hyper-V Virtual Machine Management Service (vmms.exe) thread starvation.", "Problem: ")
    add_body(doc, "Replaced unbounded recursive searches with deterministic fast-path probing using Win32 where.exe and explicit well-known PATH lists, coupled with 15-second non-interactive execution timeouts. Audit execution dropped from >12 minutes to <12 seconds.", "Resolution: ")

    add_h2(doc, "2.2 Exclusive File Locks on VHDX Chains (vmms.exe)")
    add_body(doc, "Image verification scripts attempting to hash VHDX files or differencing disks (.avhdx) failed with SharingViolationException because vmms.exe maintains active locks.", "Problem: ")
    add_body(doc, "Implemented non-blocking SHA-256 stream readers with explicit [System.IO.FileShare]::ReadWrite flags, allowing parent chain bit-verification without interrupting active standby VM pools.", "Resolution: ")

    add_h1(doc, "3. State & Memory Management: Sub-300ms Latency")
    add_h2(doc, "3.1 Cold Boot vs. Paused RAM States")
    add_body(doc, "Windows Server 2025 standard cold boot requires 14–28 seconds before accepting socket traffic on port 8080—severely breaching sub-second SLAs.", "Problem: ")
    add_body(doc, "Combining pre-allocated differencing disks with the immutable baseline-hot-ready checkpoint allows VMs to reside in paused RAM states with pre-warmed memory heaps. Resuming via Resume-VM executes in 180ms–290ms.", "Resolution: ")

    add_h2(doc, "3.2 Memory Optimization via Working Set Pre-Trimming")
    add_body(doc, "VMs captured immediately after workload initialization retained dirty working sets, inflating snapshot sizes and consuming unnecessary host RAM.", "Problem: ")
    add_body(doc, "Integrated Win32 EmptyWorkingSet P/Invoke calls prior to capturing the baseline checkpoint, reducing standby memory footprint to <700 MB RAM per instance and tripling host VM density.", "Resolution: ")

    add_h1(doc, "4. Stateful Cryptographic & Temporal Entropy")
    add_h2(doc, "4.1 Cryptographic Entropy Replay Vulnerabilities")
    add_body(doc, "Resuming an operating system from a frozen RAM state restores exact memory registers and PRNG seeds, causing subsequent requests to generate identical cryptographic salts and nonces.", "Vulnerability: ")
    add_body(doc, "Integrated a post-resume hook calling BCryptGenRandom with BCRYPT_USE_SYSTEM_PREFERRED_RNG, injecting fresh hardware entropy into the guest kernel on every wakeup cycle.", "Resolution: ")

    add_h2(doc, "4.2 Guest Real-Time Clock (RTC) Drift")
    add_body(doc, "Paused VMs freeze the guest RTC clock. Resuming after 30 minutes caused instant Kerberos token lifetime failures and TLS handshake rejections.", "Failure Mode: ")
    add_body(doc, "Leveraged Hyper-V Synthetic Clock MSR (HV_X64_MSR_TIME_REF_COUNT) and enabled Hyper-V Time Synchronization Integration Services for microsecond-level clock resynchronization upon VMBus resume.", "Resolution: ")

    add_h1(doc, "5. Stateful Zero-Trust Isolation & Port ACLs")
    add_h2(doc, "5.1 In-Guest Firewalls vs. Hypervisor-Enforced ACLs")
    add_body(doc, "Relying on in-guest Windows Defender Firewall rules creates a vulnerability: compromised workloads with elevated privileges can disable the firewall.", "Security Risk: ")
    add_body(doc, "Pushed all network isolation down to the Ring-0 Hyper-V Virtual Switch via Add-VMNetworkAdapterExtendedAcl. Default-deny egress blocks all outbound packets, with stateful whitelists restricted strictly to approved datastores (:1433, :5432), directory services (:88), and DNS (:53).", "Resolution: ")

    add_h1(doc, "6. Ingress Routing & Dynamic Scalability")
    add_h2(doc, "6.1 TCP Socket Handoff Race Conditions")
    add_body(doc, "Early proxy prototypes forwarded HTTP requests immediately upon receiving connections, racing against guest application socket readiness and triggering connection resets.", "Failure Mode: ")
    add_body(doc, "Engineered a connection-buffering gateway (jit_ingress_gateway.py) that holds the client socket open, triggers asynchronous Resume-VM, micro-probes port 8080 until SYN-ACK is confirmed, and only then proxies traffic.", "Resolution: ")

    add_h2(doc, "6.2 Sliding-Window Velocity Autoscaling (US-05 / AC-05.2)")
    add_body(doc, "A static standby pool (K=1) suffered head-of-line blocking during traffic spikes: request 1 consumed the single warm VM, forcing request 2 to wait for cold replenishment.", "Bottleneck: ")
    add_body(doc, "Implemented sliding-window velocity tracking over a 5-second window. When request rate exceeds 10 req/s, the gateway triggers burst scaling from K_min=1 to K_max=5, absorbing traffic spikes seamlessly.", "Resolution: ")

    add_h1(doc, "7. Autonomous Operations & FastMCP Tooling")
    add_body(doc, "AI agents interacting with Hyper-V through ad-hoc PowerShell commands suffered escaping bugs, permission mismatches, and syntax errors. Developed a dedicated FastMCP server (mxc_mcp_server.py) exposing high-level, schema-validated primitives (hyperv_pool_list, hyperv_pool_warm, hyperv_gateway_status, hyperv_port_acls) for safe, idempotent automation.")

    add_h1(doc, "8. Architectural Anti-Patterns & Principles")
    add_styled_table(
        doc,
        ["Anti-Pattern Discovered", "Operational Consequence", "Modern Engineering Standard Implemented"],
        [
            ["Unbounded File Traversal", "Thread exhaustion, host UI freeze, VMBus RPC lockup", "Strict fast-path lookup (where.exe), targeted probes (<15s)"],
            ["In-Guest Software Firewalls", "Bypassable by compromised guest workloads", "Ring-0 Hyper-V Virtual Switch Extended Port ACLs (ADR-005)"],
            ["Cold-Booting On-Demand", "14–28s latency, SLA breach", "Paused RAM states from baseline-hot-ready (<300ms TTFB)"],
            ["Static Pool Sizing (K=1)", "Head-of-line blocking during traffic bursts", "Sliding-window velocity autoscaler (K_min -> K_max)"],
            ["Exclusive VHDX File Locks", "SharingViolationException during live audits", "Non-blocking shared stream handles (FileShare.ReadWrite)"],
            ["Frozen Temporal Entropy", "Kerberos token failures, TLS handshakes abort", "Synthetic MSR clock sync & BCryptGenRandom re-seeding"],
            ["Raw Ad-hoc Agent Commands", "Quoting bugs, syntax errors, state drift", "Typed FastMCP schema-validated tool primitives"]
        ]
    )

    add_callout(
        doc,
        "Forward Roadmap:\n"
        "1. Host-Wide Non-Volatile Memory (NVDIMM-N): Eliminating differencing disk commit latency by mapping checkpoints to persistent RAM.\n"
        "2. Confidential Virtual Machines (CVM): Hardware-backed AMD SEV-SNP / Intel TDX memory encryption for multi-tenant hypervisors.\n"
        "3. Multi-Host Anycast Mesh: Synchronizing standby pool states across physically distributed edge hypervisors."
    )


def generate_lessons_learned():
    doc = init_doc(
        "Engineering Retrospective & Lessons Learned",
        "Low-Level Discoveries, Architectural Breakthroughs, and Hardening Standards for the MXC Hyper-V JIT Platform"
    )
    build_lessons_learned_content(doc)
    return doc


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Target Output Directory: {OUTPUT_DIR}")

    tasks = [
        ("ARCHITECTURE_DESIGN_DOCUMENT-v2.docx", generate_master_add),
        ("ARCHITECTURE_DESIGN_DOCUMENT_Merged.docx", generate_merged_master_document),
        ("BDR_Enterprise_Architecture-v2.docx", generate_bdr),
        ("ADR_Enterprise_Architecture-v2.docx", generate_adr),
        ("FDD_Enterprise_Architecture-v2.docx", generate_fdd),
        ("UserStories_Enterprise_Architecture-v2.docx", generate_user_stories),
        ("LESSONS_LEARNED_Enterprise_Architecture.docx", generate_lessons_learned),
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

