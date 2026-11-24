"""
generate_executive_summary_pdf.py

Generates an executive-grade, CBA Consult-styled A4 PDF from the MXC
Executive Summary using headless Microsoft Edge / Google Chrome (--print-to-pdf).

Output:
    docs/project-docs/Executive-Summary-MXC-Achievements.pdf
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = REPO_ROOT / "docs" / "project-docs" / "Executive-Summary-MXC-Achievements.pdf"

BROWSER_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

HTML_DOCUMENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>CBA Consult — MXC Executive Summary</title>
<style>
  @page {
    size: A4 portrait;
    margin: 13mm 14mm 16mm 14mm;
    @top-left { content: ""; }
    @top-center { content: ""; }
    @top-right { content: ""; }
    @bottom-left {
      content: "CBA Consult  |  MXC Platform Executive Summary";
      font-family: "Segoe UI", Calibri, Arial, sans-serif;
      font-size: 8pt;
      color: #64748B;
    }
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-family: "Segoe UI", Calibri, Arial, sans-serif;
      font-size: 8pt;
      color: #64748B;
    }
  }

  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  body {
    margin: 0;
    padding: 0;
    font-family: "Segoe UI", Calibri, -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 9.4pt;
    line-height: 1.45;
    color: #1E293B;
    background: #FFFFFF;
  }

  /* Cover Masthead Banner */
  .masthead {
    background: linear-gradient(135deg, #0F2942 0%, #1F4E79 62%, #1B6CA8 100%);
    color: #FFFFFF;
    padding: 14px 20px 12px 20px;
    margin: 0 0 11px 0;
    border-radius: 8px;
    border-bottom: 4px solid #0EA5E9;
  }

  .masthead-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 11px;
  }

  .brand-badge {
    width: 36px;
    height: 36px;
    border-radius: 6px;
    background: #FFFFFF;
    color: #0F2942;
    font-weight: 800;
    font-size: 13pt;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }

  .brand-text {
    display: flex;
    flex-direction: column;
  }

  .brand-name {
    font-size: 13pt;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    line-height: 1.1;
  }

  .brand-tagline {
    font-size: 7.8pt;
    color: #BAE6FD;
    letter-spacing: 0.4px;
    margin-top: 2px;
  }

  .doc-pill {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(186, 230, 253, 0.45);
    color: #E0F2FE;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: 7.8pt;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  .masthead h1 {
    margin: 0 0 6px 0;
    font-size: 19pt;
    font-weight: 700;
    letter-spacing: -0.3px;
    line-height: 1.18;
    color: #FFFFFF;
  }

  .masthead .subtitle {
    margin: 0 0 14px 0;
    font-size: 10.2pt;
    color: #E2E8F0;
    font-weight: 400;
  }

  .meta-strip {
    display: flex;
    flex-wrap: nowrap;
    justify-content: space-between;
    gap: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    font-size: 7.6pt;
    color: #CBD5E1;
  }

  .meta-strip strong {
    color: #FFFFFF;
    font-weight: 600;
  }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 14px 0 18px 0;
    break-inside: avoid;
  }

  .kpi-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #1F4E79;
    border-radius: 6px;
    padding: 10px 12px;
  }

  .kpi-card.accent {
    border-top-color: #0EA5E9;
  }

  .kpi-value {
    font-size: 15pt;
    font-weight: 800;
    color: #0F2942;
    line-height: 1.15;
  }

  .kpi-label {
    font-size: 7.6pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #475569;
    margin-top: 3px;
  }

  .kpi-sub {
    font-size: 7.4pt;
    color: #64748B;
    margin-top: 2px;
  }

  /* Section Headings */
  h2 {
    font-size: 12.2pt;
    font-weight: 700;
    color: #0F2942;
    margin: 16px 0 7px 0;
    padding-bottom: 4px;
    border-bottom: 2px solid #1F4E79;
    display: flex;
    align-items: center;
    gap: 7px;
    break-after: avoid;
  }

  .sec-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 4px;
    background: #1F4E79;
    color: #FFFFFF;
    font-size: 8.5pt;
    font-weight: 700;
  }

  h3 {
    font-size: 10pt;
    font-weight: 700;
    color: #1F4E79;
    margin: 11px 0 5px 0;
    break-after: avoid;
  }

  p {
    margin: 0 0 8px 0;
  }

  /* Callout Box */
  .callout {
    background: #F0F9FF;
    border-left: 4px solid #0284C7;
    border-radius: 0 6px 6px 0;
    padding: 10px 13px;
    margin: 10px 0 12px 0;
    break-inside: avoid;
  }

  .callout-title {
    font-weight: 700;
    color: #0369A1;
    font-size: 9.2pt;
    margin-bottom: 4px;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 5px 0 8px 0;
    font-size: 7.9pt;
    line-height: 1.3;
  }

  tr {
    break-inside: avoid;
  }

  th {
    background: #0F2942;
    color: #FFFFFF;
    font-weight: 600;
    text-align: left;
    padding: 4.5px 7px;
    border: 1px solid #0F2942;
  }

  td {
    padding: 4px 7px;
    border: 1px solid #CBD5E1;
    vertical-align: top;
  }

  tr:nth-child(even) td {
    background: #F8FAFC;
  }

  .badge {
    display: inline-block;
    padding: 1.5px 7px;
    border-radius: 999px;
    font-size: 7.3pt;
    font-weight: 700;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .badge-pass {
    background: #DCFCE7;
    color: #166534;
    border: 1px solid #86EFAC;
  }

  .badge-phase2 {
    background: #E0F2FE;
    color: #075985;
    border: 1px solid #7DD3FC;
  }

  .badge-planned {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FCD34D;
  }

  code {
    font-family: Consolas, "Cascadia Code", monospace;
    font-size: 8.2pt;
    background: #F1F5F9;
    color: #0F2942;
    padding: 1px 4px;
    border-radius: 3px;
  }

  ul {
    margin: 4px 0 10px 0;
    padding-left: 18px;
  }

  li {
    margin-bottom: 4px;
  }

  /* Two-column cards for Next Features */
  .roadmap-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 8px 0 14px 0;
    break-inside: avoid;
  }

  .roadmap-card {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 10px 11px;
  }

  .roadmap-card h4 {
    margin: 0 0 6px 0;
    font-size: 8.8pt;
    font-weight: 700;
    color: #0F2942;
    padding-bottom: 4px;
    border-bottom: 2px solid #0EA5E9;
  }

  .roadmap-card ul {
    margin: 0;
    padding-left: 14px;
    font-size: 8.2pt;
  }

  .roadmap-card li {
    margin-bottom: 4px;
  }

  /* Call to Action Box */
  .cta-box {
    background: linear-gradient(135deg, #0F2942 0%, #1F4E79 100%);
    color: #FFFFFF;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 12px;
    border-left: 5px solid #38BDF8;
    break-inside: avoid;
  }

  .cta-box h3 {
    margin: 0 0 6px 0;
    color: #38BDF8;
    font-size: 11pt;
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }

  .cta-box p {
    color: #E2E8F0;
    font-size: 8.9pt;
    margin-bottom: 8px;
  }

  .cta-tracks {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 9px;
    margin-top: 8px;
  }

  .cta-track {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(186, 230, 253, 0.35);
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 8.1pt;
    color: #F1F5F9;
  }

  .cta-track strong {
    display: block;
    color: #7DD3FC;
    margin-bottom: 3px;
    font-size: 8.4pt;
  }

  .page-break {
    page-break-before: always;
  }
</style>
</head>
<body>

  <!-- CBA Consult Masthead -->
  <div class="masthead">
    <div class="masthead-top">
      <div class="brand-lockup">
        <div class="brand-badge">CBA</div>
        <div class="brand-text">
          <span class="brand-name">CBA Consult</span>
          <span class="brand-tagline">Enterprise Architecture &amp; Cloud Engineering</span>
        </div>
      </div>
      <div class="doc-pill">Executive Summary &amp; Feature Intake</div>
    </div>
    <h1>MXC Micro-Execution Container Platform</h1>
    <div class="subtitle">Verified Achievements (Phases 1 &amp; 2), Complete Capability Inventory &amp; Next-Phase Call to Action</div>
    <div class="meta-strip">
      <span><strong>Date:</strong> 23 November 2026</span>
      <span><strong>Branch:</strong> feat/hyperv-v2-rebased</span>
      <span><strong>Baselines:</strong> PMP-BL-v1.0.0 (Closed) &bull; PMP-BL-v2.0.0 (Active)</span>
      <span><strong>Governance:</strong> SIDPA / PMBOK 8</span>
    </div>
  </div>

  <!-- Executive KPI Strip -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-value">9 / 9</div>
      <div class="kpi-label">Epics Delivered</div>
      <div class="kpi-sub">Phase 1 (001–006) &amp; Phase 2 (007–009)</div>
    </div>
    <div class="kpi-card accent">
      <div class="kpi-value">271 / 271</div>
      <div class="kpi-label">Automated Tests</div>
      <div class="kpi-sub">188 Python contracts + 83 Rust SDK</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-value">&le; 5 ms</div>
      <div class="kpi-label">Hot SLA Dispatch</div>
      <div class="kpi-sub">1.5 ms Hot &bull; &le; 250 ms Warm &bull; 0 MB Cold</div>
    </div>
    <div class="kpi-card accent">
      <div class="kpi-value">100%</div>
      <div class="kpi-label">Parent Sterility</div>
      <div class="kpi-sub">Live Gen2 Hyper-V E2E verified</div>
    </div>
  </div>

  <!-- Section 1 -->
  <h2><span class="sec-num">1</span> Executive Overview &amp; Strategic Differentiator</h2>
  <p>
    The <strong>MXC (Micro-Execution Container)</strong> platform has progressed from architectural blueprint to a
    <strong>verified, hardware-isolated multi-tier execution fabric</strong>. Across Phase 1 (closed) and Phase 2 (active),
    MXC proves that full native Windows Server 2025 and Windows 11 micro-VMs can be dispatched at container-like speeds
    with zero daemon bloat, strict hypervisor isolation, and byte-for-byte immutable golden base images.
  </p>

  <div class="callout">
    <div class="callout-title">Why MXC Instead of Standard Docker Containers?</div>
    Standard Docker containers share the host kernel, rely on a privileged daemon, and cannot run native Windows GUI/Desktop
    workloads or mismatched OS builds cleanly. MXC unifies <strong>10 containment backends</strong> under one declarative policy
    contract—combining <strong>Type-1 Hyper-V Gen2 micro-VMs</strong>, daemonless OS sandboxes (<code>processcontainer</code>,
    <code>windows_sandbox</code>, <code>seatbelt</code>, <code>bubblewrap</code>), and OCI runtimes (<code>wslc</code>, <code>lxc</code>)
    with airgapped VMBus execution (<strong>PowerShell Direct</strong>) and sub-second warm standby pools.
  </div>

  <!-- Section 2 -->
  <h2><span class="sec-num">2</span> Delivered Platform Capabilities (Epics 001–009)</h2>

  <table>
    <thead>
      <tr>
        <th style="width: 11%;">Epic</th>
        <th style="width: 26%;">Capability</th>
        <th style="width: 12%;">Phase</th>
        <th style="width: 51%;">Verified Architectural &amp; Functional Delivery</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Epic 001</strong></td>
        <td>Type-1 Hyper-V Gen2 Isolation</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Hardware-virtualized Gen2 micro-VMs replacing shared-kernel namespaces; automated Windows subsystem verification.</td>
      </tr>
      <tr>
        <td><strong>Epic 002</strong></td>
        <td>Connection-Buffering Ingress</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Ingress gateway buffers incoming TCP/HTTP client connections during JIT wake-up for zero dropped requests.</td>
      </tr>
      <tr>
        <td><strong>Epic 003</strong></td>
        <td>Production Base Image Supply</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Strict dev/prod golden VHDX separation, offline compliance audit gate (zero unauthorized dev tools), and baseline checkpoints.</td>
      </tr>
      <tr>
        <td><strong>Epic 004</strong></td>
        <td>Paused RAM Standby &amp; Trimming</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Pre-suspend guest working-set trimming holding warm-paused Windows Server instances at ~1.0–1.2 GB RAM (~215 ms unpause).</td>
      </tr>
      <tr>
        <td><strong>Epic 005</strong></td>
        <td>Differencing Disk &amp; Sterility</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Per-session transient differencing VHDX off read-only parents, egress whitelisting, and clean discard with parent invariance.</td>
      </tr>
      <tr>
        <td><strong>Epic 006</strong></td>
        <td>Watermark Pool &amp; Wake Hygiene</td>
        <td><span class="badge badge-pass">Phase 1</span></td>
        <td>Automated standby replenishment, non-blocking background refill, and triple-gate wake hygiene preventing surge exhaustion.</td>
      </tr>
      <tr>
        <td><strong>Epic 007</strong></td>
        <td>Multi-Tier Standby Pools</td>
        <td><span class="badge badge-phase2">Phase 2</span></td>
        <td>3-tier SLA fleet: <code>HotRunning</code> (&le; 5 ms), <code>WarmPaused</code> (&le; 250 ms), <code>ColdSaved</code> (0 MB RAM on NVMe) + dynamic idle demotion.</td>
      </tr>
      <tr>
        <td><strong>Epic 008</strong></td>
        <td>Predictive Wake &amp; Forecasting</td>
        <td><span class="badge badge-phase2">Phase 2</span></td>
        <td>Early TLS ClientHello SNI pre-wake concurrency plus time-series activity forecasting for near-0 ms perceived wake.</td>
      </tr>
      <tr>
        <td><strong>Epic 009</strong></td>
        <td>Host Memory Combining</td>
        <td><span class="badge badge-phase2">Phase 2</span></td>
        <td>Hyper-V host page deduplication probe, copy-on-write (COW) tenant isolation check, and saturation density floor verification.</td>
      </tr>
    </tbody>
  </table>

  <!-- Page 2 -->
  <div class="page-break"></div>

  <h2><span class="sec-num">3</span> Live Host Validation, SDK &amp; Governance Assurance</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 28%;">Verification Layer</th>
        <th style="width: 14%;">Status</th>
        <th style="width: 58%;">Evidence &amp; Operational Proof</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Rust SDK (<code>mxc-sdk</code> / <code>wxc-exec</code>)</strong></td>
        <td><span class="badge badge-pass">83 / 83 PASS</span></td>
        <td>Full 5-phase lifecycle (<code>provision</code>, <code>start</code>, <code>exec</code>, <code>stop</code>, <code>deprovision</code>), <code>pool-*</code>, <code>checkpoint</code>/<code>restore</code>, <code>pause</code>/<code>resume</code>, Credential Manager zeroize.</td>
      </tr>
      <tr>
        <td><strong>Python Contract Suite</strong></td>
        <td><span class="badge badge-pass">188 / 188 PASS</span></td>
        <td>End-to-end contract verification across all 9 Epics, spec gates, SLA dispatch bounds, TLS pre-wake, and memory combining.</td>
      </tr>
      <tr>
        <td><strong>Live Hyper-V Micro-VM E2E</strong></td>
        <td><span class="badge badge-pass">VERIFIED</span></td>
        <td>Provisioned Gen2 Windows Server 2025 working copy from <code>F:\HyperV\BaseImages</code>, verified 8/8 VMIC services via PowerShell Direct, confirmed parent VHDX untouched, cleanly deprovisioned.</td>
      </tr>
      <tr>
        <td><strong>Multi-Backend Host Probe</strong></td>
        <td><span class="badge badge-pass">3 ACTIVE</span></td>
        <td><code>hyperv</code>, <code>processcontainer</code> (UI isolation + <code>--audit</code>), and <code>windows_sandbox</code> active on host; 7 additional cross-platform backends in SDK.</td>
      </tr>
      <tr>
        <td><strong>SIDPA / PMBOK 8 Governance</strong></td>
        <td><span class="badge badge-pass">COMPLIANT</span></td>
        <td>Full traceability across ADRs 001–011, BRDs, FDDs, User Stories, Audits (<code>AUDIT-001..009</code>), Lessons Learned (<code>LL-001..010</code>), and 16 improvement candidates (<code>IMP-MXC-001..016</code>).</td>
      </tr>
    </tbody>
  </table>

  <!-- Section 4 -->
  <h2><span class="sec-num">4</span> Logical Next Features &amp; Candidate Roadmap</h2>
  <p>
    Live host verification and our Continuous Improvement Register surfaced three cohesive groups of logical next features
    ready for stakeholder prioritization:
  </p>

  <div class="roadmap-grid">
    <div class="roadmap-card">
      <h4>A. Planned Phase 2 Completion</h4>
      <ul>
        <li><strong>Epic 010 — Signed Image Supply Chain &amp; SLSA:</strong> Cryptographic VHDX signatures, SPDX/CycloneDX SBOMs, and pre-dispatch attestation gate (<code>IMP-MXC-003/010</code>).</li>
        <li><strong>Epic 011 — Autonomous Fleet Economics:</strong> Closed-loop scheduler optimizing cost-per-session, wake SLA, and host RAM saturation (<code>IMP-MXC-011</code>).</li>
      </ul>
    </div>
    <div class="roadmap-card">
      <h4>B. Live Runtime Hardening (Rust)</h4>
      <ul>
        <li><strong>Multi-Tier Rust Parity:</strong> Port Hot/Warm/Cold pools &amp; predictive wake from Python into <code>wxc-exec</code> / <code>mxc-sdk</code>.</li>
        <li><strong>Image-Aware Resource Profiles:</strong> Enforce per-image RAM (static vs. dynamic), vCPU, and NVMe/Archive storage tiers automatically.</li>
        <li><strong><code>--wait-ready</code> Boot Gate:</strong> Wait for Heartbeat + PowerShell Direct readiness inside <code>wxc-exec start</code>.</li>
      </ul>
    </div>
    <div class="roadmap-card">
      <h4>C. Phase 3 Innovation Candidates</h4>
      <ul>
        <li><strong>512–640 MB Ultra-Lean Bake:</strong> Server Core stripping to nearly double fleet density (<code>IMP-MXC-006</code>).</li>
        <li><strong>RAM-Disk / DAX Differencing:</strong> Sub-microsecond ephemeral I/O with zero NVMe wear (<code>IMP-MXC-012</code>).</li>
        <li><strong>Kernel TLS Snooping (eBPF/WFP):</strong> Root-partition pre-wake promotion (<code>IMP-MXC-014/015</code>).</li>
        <li><strong>Subsystem Telemetry Matrix:</strong> Pre-dispatch WMI/COM+/Service health streaming (<code>IMP-MXC-001</code>).</li>
      </ul>
    </div>
  </div>

  <!-- Section 5: Call to Action -->
  <div class="cta-box">
    <h3>Call to Action — Shape the Next Wave of MXC Delivery</h3>
    <p>
      We invite architecture leads, product owners, and platform stakeholders to submit <strong>additional feature requests</strong>,
      flag workload-specific requirements (security, networking, clustering, developer UX), and rank the logical next features above
      (<strong>Must-Have / Should-Have / Defer</strong>) to confirm our next execution track:
    </p>
    <div class="cta-tracks">
      <div class="cta-track">
        <strong>Track 1: Complete Phase 2</strong>
        Draft &amp; deliver planned Epics 010 (SLSA Supply Chain) and 011 (Autonomous Fleet Economics), then run formal Phase 2 closeout.
      </div>
      <div class="cta-track">
        <strong>Track 2: Harden Live Runtime</strong>
        Prioritize Rust runtime parity for multi-tier pools, image-aware RAM/CPU profiles, and <code>--wait-ready</code> boot gating first.
      </div>
      <div class="cta-track">
        <strong>Track 3: Launch Phase 3 Ideation</strong>
        Close Phase 2 at Epic 009 and fold all selected features &amp; stakeholder requests into a fresh Phase 3 Spark Capture &amp; Baseline.
      </div>
    </div>
  </div>

</body>
</html>
"""


def find_browser() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    for name in ("msedge", "chrome"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise FileNotFoundError("Neither Microsoft Edge nor Google Chrome was found for headless PDF rendering.")


def main() -> int:
    browser = find_browser()
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "executive_summary.html"
        html_path.write_text(HTML_DOCUMENT, encoding="utf-8")

        cmd = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={OUTPUT_PDF}",
            html_path.as_uri(),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or not OUTPUT_PDF.exists():
            print(f"PDF generation failed (rc={result.returncode}): {result.stderr}", file=sys.stderr)
            return 1

    size_kb = OUTPUT_PDF.stat().st_size / 1024
    print(f"Generated CBA Consult PDF: {OUTPUT_PDF} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
