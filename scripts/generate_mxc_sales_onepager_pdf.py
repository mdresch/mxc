"""
generate_mxc_sales_onepager_pdf.py

Generates a crisp, single-page CBa Consult-styled A4 Sales One-Pager PDF for MXC
using headless Microsoft Edge / Google Chrome (--print-to-pdf).

Output:
    docs/marketing/MXC-Product-One-Pager.pdf
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = REPO_ROOT / "docs" / "marketing" / "MXC-Product-One-Pager.pdf"

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
<title>CBa Consult — MXC Product One-Pager</title>
<style>
  @page {
    size: A4 portrait;
    margin: 11mm 13mm 13mm 13mm;
    @top-left { content: ""; }
    @top-center { content: ""; }
    @top-right { content: ""; }
    @bottom-left {
      content: "CBa Consult  |  MXC Micro-Execution Container — Product Sales One-Pager";
      font-family: "Segoe UI", Calibri, Arial, sans-serif;
      font-size: 7.5pt;
      color: #64748B;
    }
    @bottom-right {
      content: "cbaconsult.nl  |  Menno Drescher";
      font-family: "Segoe UI", Calibri, Arial, sans-serif;
      font-size: 7.5pt;
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
    font-size: 8.7pt;
    line-height: 1.38;
    color: #1E293B;
    background: #FFFFFF;
  }

  .masthead {
    background: linear-gradient(135deg, #0F2942 0%, #1F4E79 62%, #1B6CA8 100%);
    color: #FFFFFF;
    padding: 14px 20px 13px 20px;
    margin: 0 0 10px 0;
    border-radius: 8px;
    border-bottom: 4px solid #0EA5E9;
  }

  .masthead-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-badge {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: #FFFFFF;
    color: #0F2942;
    font-weight: 800;
    font-size: 11.5pt;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .brand-name {
    font-size: 11.5pt;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    display: block;
    line-height: 1.1;
  }

  .brand-tagline {
    font-size: 7.3pt;
    color: #BAE6FD;
    display: block;
  }

  .doc-pill {
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(186, 230, 253, 0.45);
    color: #E0F2FE;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 7.4pt;
    font-weight: 600;
    letter-spacing: 0.4px;
    text-transform: uppercase;
  }

  .masthead h1 {
    margin: 0 0 4px 0;
    font-size: 16.5pt;
    font-weight: 700;
    line-height: 1.15;
    color: #FFFFFF;
  }

  .masthead .subtitle {
    margin: 0;
    font-size: 9.2pt;
    color: #E2E8F0;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin: 0 0 10px 0;
  }

  .kpi-card {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-top: 3px solid #1F4E79;
    border-radius: 6px;
    padding: 7px 9px;
  }

  .kpi-card.accent { border-top-color: #0EA5E9; }
  .kpi-val { font-size: 13pt; font-weight: 800; color: #0F2942; line-height: 1.1; }
  .kpi-lbl { font-size: 7pt; font-weight: 700; text-transform: uppercase; color: #475569; margin-top: 2px; }
  .kpi-sub { font-size: 6.9pt; color: #64748B; margin-top: 1px; }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 9px;
  }

  .box {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 11px;
  }

  .box.problem { border-left: 4px solid #DC2626; background: #FEF2F2; }
  .box.solution { border-left: 4px solid #0284C7; background: #F0F9FF; }

  .box h3 {
    margin: 0 0 4px 0;
    font-size: 9pt;
    font-weight: 700;
    color: #0F2942;
  }

  .box ul { margin: 0; padding-left: 15px; font-size: 8.1pt; }
  .box li { margin-bottom: 3px; }

  h2 {
    font-size: 10.5pt;
    font-weight: 700;
    color: #0F2942;
    margin: 9px 0 5px 0;
    padding-bottom: 3px;
    border-bottom: 2px solid #1F4E79;
  }

  .feat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 9px;
  }

  .feat-card {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-top: 3px solid #0EA5E9;
    border-radius: 6px;
    padding: 7px 9px;
    font-size: 7.8pt;
  }

  .feat-card strong {
    display: block;
    color: #0F2942;
    font-size: 8.2pt;
    margin-bottom: 2px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 9px 0;
    font-size: 7.8pt;
  }

  th {
    background: #0F2942;
    color: #FFFFFF;
    text-align: left;
    padding: 4.5px 7px;
    border: 1px solid #0F2942;
  }

  td {
    padding: 4px 7px;
    border: 1px solid #CBD5E1;
    vertical-align: top;
  }

  tr:nth-child(even) td { background: #F8FAFC; }

  .cta-bar {
    background: linear-gradient(135deg, #0F2942 0%, #1F4E79 100%);
    color: #FFFFFF;
    border-radius: 7px;
    padding: 10px 14px;
    border-left: 5px solid #38BDF8;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
  }

  .cta-bar h4 { margin: 0 0 2px 0; color: #38BDF8; font-size: 9.2pt; text-transform: uppercase; letter-spacing: 0.4px; }
  .cta-bar p { margin: 0; font-size: 8pt; color: #E2E8F0; }
  .cta-pill {
    background: #38BDF8;
    color: #0F2942;
    font-weight: 800;
    font-size: 8pt;
    padding: 7px 12px;
    border-radius: 6px;
    white-space: nowrap;
  }
</style>
</head>
<body>

  <div class="masthead">
    <div class="masthead-top">
      <div class="brand-lockup">
        <div class="brand-badge">CBa</div>
        <div>
          <span class="brand-name">CBa Consult</span>
          <span class="brand-tagline">Enterprise Architecture &amp; Sovereign AI Execution</span>
        </div>
      </div>
      <div class="doc-pill">Product Sales One-Pager</div>
    </div>
    <h1>MXC — Micro-Execution Container</h1>
    <div class="subtitle">Hardware-Isolated Windows 11, Windows Server 2025 &amp; AI Agent Sandboxes — at Container Speed</div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-val">&le; 5 ms</div>
      <div class="kpi-lbl">Hot SLA Dispatch</div>
      <div class="kpi-sub">1.5 ms Hot &bull; &le; 250 ms Warm &bull; 0 MB Cold</div>
    </div>
    <div class="kpi-card accent">
      <div class="kpi-val">9 sec</div>
      <div class="kpi-lbl">Win11 Cold Boot</div>
      <div class="kpi-sub">Prompt-only shell &bull; 12 agent tools</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val">0 NICs</div>
      <div class="kpi-lbl">Airgapped Default</div>
      <div class="kpi-sub">VMBus PowerShell Direct + file transfer</div>
    </div>
    <div class="kpi-card accent">
      <div class="kpi-val">100%</div>
      <div class="kpi-lbl">Session Sterility</div>
      <div class="kpi-sub">271/271 tests &bull; Zero parent mutation</div>
    </div>
  </div>

  <div class="two-col">
    <div class="box problem">
      <h3>The Problem: Containers Fail AI Agents &amp; Windows</h3>
      <ul>
        <li><strong>Shared-Kernel Risk:</strong> Docker shares the host kernel—unacceptable blast radius for untrusted AI-generated code.</li>
        <li><strong>Windows Fidelity Wall:</strong> Linux containers cannot run native Windows 11, Win32/COM, or mismatched Windows Server builds.</li>
        <li><strong>VM Bloat &amp; Drift:</strong> Traditional VMs take minutes to boot, waste idle RAM, and leak state across runs.</li>
      </ul>
    </div>
    <div class="box solution">
      <h3>The MXC Breakthrough: Type-1 Speed + Zero-Trust</h3>
      <ul>
        <li><strong>True Hypervisor Isolation:</strong> Type-1 Hyper-V Gen2 micro-VMs + 10 unified backends under one declarative policy contract.</li>
        <li><strong>Airgapped VMBus Control:</strong> Execute commands &amp; transfer files with zero network adapter and zero guest-stored secrets.</li>
        <li><strong>On-Prem / EU Sovereign:</strong> Runs on your existing Hyper-V / Azure Local hardware—€0 third-party sandbox SaaS fees.</li>
      </ul>
    </div>
  </div>

  <h2>Core Platform Capabilities</h2>
  <div class="feat-grid">
    <div class="feat-card">
      <strong>1. Multi-Tier Standby Pools</strong>
      Routes workloads across <code>HotRunning</code> (&le;5 ms), <code>WarmPaused</code> (&le;250 ms), and <code>ColdSaved</code> (0 MB RAM) with auto idle demotion.
    </div>
    <div class="feat-card">
      <strong>2. Predictive Wake &amp; Zero-Drop Ingress</strong>
      TLS SNI interception + activity forecasting wake micro-VMs ahead of demand while buffering TCP connections cleanly.
    </div>
    <div class="feat-card">
      <strong>3. Speculative Execution &amp; Rollback</strong>
      Snapshot clean baselines, let agents mutate/test code, and roll back destructive changes in seconds or erase differencing disks on exit.
    </div>
    <div class="feat-card">
      <strong>4. Lean Win11 Pro Agent Image</strong>
      90 AppX bloat packages &amp; Explorer stripped; <code>git</code>, <code>gh</code>, <code>pwsh 7</code>, <code>python 3.15</code>, <code>uv</code>, <code>ruff</code>, <code>pytest</code>, <code>node 26</code>, <code>tsc 7</code> pre-baked.
    </div>
    <div class="feat-card">
      <strong>5. Host Memory Combining</strong>
      Deduplicates identical Windows kernel &amp; runtime pages across concurrent micro-VMs with verified Copy-on-Write isolation.
    </div>
    <div class="feat-card">
      <strong>6. EU AI Act &amp; Audit Readiness</strong>
      Immutable golden parents + verifiable execution trails aligned to EU AI Act Annex III (Dec 2, 2027, Reg. EU 2026/1744) &amp; ISO 42001.
    </div>
  </div>

  <h2>Enterprise Use Cases &amp; Engagement Path</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 24%;">Engagement Tier</th>
        <th style="width: 18%;">Timeline</th>
        <th style="width: 58%;">Target Use Cases &amp; Concrete Deliverables</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Phase 0 — Live PoC</strong></td>
        <td>2–4 Weeks</td>
        <td>Deploy MXC Hyper-V runtime + custom hardened golden agent image on your host; prove &lt;250 ms warm wake, airgapped VMBus exec &amp; checkpoint rollback on a live workload.</td>
      </tr>
      <tr>
        <td><strong>Production Fabric Rollout</strong></td>
        <td>6–10 Weeks</td>
        <td>Multi-tier Hot/Warm/Cold pools, connection-buffering ingress gateway, automated image compliance audit, and CISO zero-trust sign-off pack.</td>
      </tr>
      <tr>
        <td><strong>MIP Retainer (<code>OP-ITG-018</code>)</strong></td>
        <td>Ongoing Monthly</td>
        <td>Continuous pool hygiene, golden image patching, Agent FinOps, and EU AI Act / ISO 42001 pre-assurance alongside your MSP &amp; MSSP.</td>
      </tr>
    </tbody>
  </table>

  <div class="cta-bar">
    <div>
      <h4>See MXC Live in 15 Minutes</h4>
      <p>Watch an airgapped Windows 11 Lean Agent VM boot in 9s, execute polyglot tests over VMBus, survive a simulated rogue mutation via checkpoint rollback, and sterilize cleanly.</p>
    </div>
    <div class="cta-pill">Book Live Demo &rarr; CBa Consult</div>
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
    raise FileNotFoundError("Neither Microsoft Edge nor Google Chrome found.")


def main() -> int:
    browser = find_browser()
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "mxc_onepager.html"
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
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode != 0 or not OUTPUT_PDF.exists():
            print(f"PDF generation failed: {res.stderr}", file=sys.stderr)
            return 1
    print(f"Generated 1-Page Sales PDF: {OUTPUT_PDF} ({OUTPUT_PDF.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
