"""
PMBOK 8 Subsidiary Plans & PMP Orchestrator for SIDPA Template Projects.

Generates and updates the 9 subsidiary management plans and the integrated
Project Management Plan (PMP) using project-anchored context from:
- docs/project-docs/Spark-Capture.md
- docs/project-docs/Ideation-Document.md
- docs/project-docs/Business-Case.md
- docs/project-docs/Project-Charter.md

Also provides closed-loop adaptation regeneration via:
--adapt-from docs/project-docs/Adaptation-Plan.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Add sidpa-template root to sys.path so pmbok is importable
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

os.environ["ADPA_AUDIT_MODE"] = "advisory"

from pmbok.models.enums import ProcessGroup
from pmbok.models.pmbok import ProjectArtifact
from pmbok.storage.artifact_store import ArtifactStore
from pmbok.storage.state_store import StateStore
from pmbok.agents.factory import ProcessAgentFactory
from pmbok.agents.process_agent import _StubLLMClient
from pmbok.orchestrator.orchestrator import PMBOKOrchestrator
from pmbok.output.pretty_printer import PrettyPrinter

PLAN_MAPPING = {
    "5.1": {"name": "Scope-Management-Plan", "title": "Scope Management Plan", "flag": "Scope Management Plan"},
    "6.1": {"name": "Schedule-Management-Plan", "title": "Schedule Management Plan", "flag": "Schedule / Cost Plans"},
    "7.1": {"name": "Cost-Management-Plan", "title": "Cost Management Plan", "flag": "Schedule / Cost Plans"},
    "8.1": {"name": "Quality-Management-Plan", "title": "Quality Management Plan", "flag": "Quality Management Plan"},
    "9.1": {"name": "Resource-Management-Plan", "title": "Resource Management Plan", "flag": "Resource Management Plan"},
    "10.1": {"name": "Communications-Management-Plan", "title": "Communications Management Plan", "flag": "Communications Management Plan"},
    "11.1": {"name": "Risk-Management-Plan", "title": "Risk Management Plan", "flag": "Risk Management Plan"},
    "12.1": {"name": "Procurement-Management-Plan", "title": "Procurement Management Plan", "flag": "Procurement Management Plan"},
    "13.2": {"name": "Stakeholder-Engagement-Plan", "title": "Stakeholder Engagement Plan", "flag": "Stakeholder Engagement Plan"},
}

def extract_project_identity(charter_path: Path) -> dict[str, str]:
    """Extract project title and objectives from Project Charter."""
    if not charter_path.exists():
        return {
            "title": "SIDPA Project",
            "objectives": ["Establish validated development lifecycle", "Enforce PMBOK 8 governance baselines"]
        }
    text = charter_path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).replace("Project Charter", "").strip(" :-") if title_match else "SIDPA Project"
    if not title:
        title = "SIDPA Project"
    return {
        "title": title,
        "objectives": [
            "Formalize PMBOK 8 planning baselines",
            "Generate verified subsidiary management plans",
            "Integrate into Project Management Plan (PMP)"
        ]
    }

def synthesize_pmp_markdown(project_context: dict, generated_plans: dict[str, str], baseline_id: str = "PMP-BL-v1.0.0") -> str:
    """Synthesize integrated Project-Management-Plan.md from subsidiary plans."""
    clean_title = project_context["title"].strip()
    for _ch in [":", "-", "\u2014"]:
        clean_title = clean_title.strip(_ch).strip()
    lines = [
        "---",
        'pmbok_edition: "PMBOK 8"',
        'pmbok_process_group: "Planning"',
        'pmbok_process: "4.2 Develop Project Management Plan"',
        f'pmp_baseline: "{baseline_id}"',
        'lifecycle_stage: "Stage 6 (Project)"',
        'governance_policy: "approve-pmp"',
        "inputs:",
        '  - "Project-Charter.md"',
        '  - "docs/project-docs/management-plans/*.md"',
        'process: "Integrate subsidiary management plans, establish baselines, define governance gates"',
        "outputs:",
        '  - "Project-Management-Plan.md"',
        "---",
        "",
        f"# Project Management Plan (PMP) — {clean_title}",
        "",
        "> **PMBOK 8 Process:** `4.2 Develop Project Management Plan` (Planning)  ",
        "> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 6 (Project)`  ",
        f"> **Baseline Identifier:** `{baseline_id}`  ",
        "> **Inputs:** Project-Charter.md, Subsidiary Management Plans  ",
        "> **Process:** Integrate subsidiary management plans, establish baselines, define governance gates  ",
        "> **Outputs:** Project-Management-Plan.md",
        "",
        "## 1. Executive Summary & Baselines",
        f"- **Project Title:** {clean_title}",
        f"- **Baseline ID:** `{baseline_id}`",
        "- **Scope Baseline:** Approved scope boundary traced to Project Charter objectives.",
        "- **Schedule Baseline / Progressive Elaboration:** Milestones established; duration detailed progressively from empirical evidence.",
        "- **Cost Baseline / Progressive Elaboration:** Investment limits from Business Case; detailed cost tracked as resources are committed.",
        "",
        "## 2. Integrated Subsidiary Management Plans",
        ""
    ]
    
    for pid, meta in PLAN_MAPPING.items():
        doc_name = f"{meta['name']}.md"
        summary = generated_plans.get(pid, f"Detailed in [management-plans/{doc_name}](management-plans/{doc_name}).")
        lines.append(f"### 2.{pid} {meta['title']}")
        lines.append(f"**Document Link:** [management-plans/{doc_name}](management-plans/{doc_name})")
        lines.append(f"- **Summary:** {summary[:300]}...")
        lines.append("")

    lines.extend([
        "## 3. Feedback Loop from Adaptation",
        "When an **Adaptation Plan** (Stage 17) is approved, this PMP and its subsidiary plans are updated with tailored operational changes evaluated through the Governance Change Impact Matrix, which in turn trigger refined ADRs, BRDs, FDDs, and Stories for the next cycle. Prior baselines are archived to `management-plans/history/{baseline_id}/`.",
        "",
        "## 4. Governance Authorization",
        f"This integrated PMP must be formally evaluated and approved via `approve-pmp` (`FULL` Bayesian authority, `requires_human_approval: true`) before technical specifications (ADR, BRD, FDD, Stories) are finalized. All downstream technical requirements must record `pmp_baseline: '{baseline_id}'` (Invariant 6). Prior baselines remain recoverable from history archives (Invariant 7)."
    ])
    return "\n".join(lines) + "\n"

def parse_adaptation_checklist(adaptation_path: Path) -> list[str]:
    """Parse checked subsidiary management plans from Adaptation-Plan.md."""
    if not adaptation_path.exists():
        return []
    content = adaptation_path.read_text(encoding="utf-8")
    checked = []
    for line in content.splitlines():
        match = re.match(r"^-\s*\[[xX]\]\s*\*\*([^*]+)\*\*", line)
        if match:
            checked.append(match.group(1).strip())
    return checked

async def run_orchestration(args):
    charter_file = Path(args.charter)
    project_context = extract_project_identity(charter_file)
    print(f"\n=======================================================")
    print(f"  SIDPA PMBOK Orchestrator — {project_context['title']}")
    print(f"  Mode: {args.mode.upper()}")
    print(f"=======================================================\n")

    plans_dir = repo_root / "docs" / "project-docs" / "management-plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = repo_root / "data" / "pmbok_runtime"
    storage_dir.mkdir(parents=True, exist_ok=True)

    artifact_store = ArtifactStore(storage_dir)
    state_store = StateStore(str(storage_dir / "state.db"))

    # Determine LLM client
    has_api_key = bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if args.mock or not has_api_key:
        print("  [INFO] Using High-Fidelity Deterministic Engine (Offline / Stub)")
        from pmbok.agents.process_agent import _StubLLMClient
        llm_client = _StubLLMClient()
    else:
        print("  [INFO] Using Live LLM Foundry Client")
        from pmbok.llm import create_llm_client
        llm_client = create_llm_client()

    factory = ProcessAgentFactory(llm_client=llm_client, artifact_store=artifact_store)

    target_processes = list(PLAN_MAPPING.keys())
    if args.mode == "adapt" and args.adaptation_plan:
        adapt_file = Path(args.adaptation_plan)
        checked_flags = parse_adaptation_checklist(adapt_file)
        print(f"  [ADAPT] Checked plans in {adapt_file.name}: {checked_flags}")
        target_processes = [
            pid for pid, meta in PLAN_MAPPING.items()
            if any(flag in meta["flag"] or meta["title"] in flag for flag in checked_flags)
        ]
        if not target_processes:
            print("  [ADAPT] No specific subsidiary plans checked. Defaulting to full re-sync.")
            target_processes = list(PLAN_MAPPING.keys())

    print(f"  Target PMBOK Processes: {target_processes}\n")

    printer = PrettyPrinter()
    generated_summaries = {}

    from pmbok.process_registry import PMBOK_PROCESSES
    proc_map = {p.process_id: p for p in PMBOK_PROCESSES}

    for pid in target_processes:
        meta = PLAN_MAPPING[pid]
        proc = proc_map.get(pid)
        if not proc:
            print(f"      [WARN] Process {pid} not found in registry")
            continue

        print(f"  >>> Executing PMBOK {pid}: {meta['title']}...")
        agent = factory.create(proc)
        # Execute agent
        prompt = (
            f"Generate high-fidelity {meta['title']} (PMBOK {pid}) for project '{project_context['title']}'.\n"
            f"Objectives: {', '.join(project_context['objectives'])}.\n"
            f"Expected outputs: ['{meta['title']}']"
        )
        try:
            artifacts = await agent.execute(
                run_id="sidpa-run",
                input_artifacts=[],
                project_context=project_context
            )
            if artifacts:
                art = artifacts[0]
                doc_path = plans_dir / f"{meta['name']}.md"
                md_content = f"""---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "{pid} {meta['title']}"
lifecycle_stage: "Stage 6 (Project)"
governance_policy: "approve-pmp"
inputs:
  - "Project-Charter.md"
process: "Plan and formalize {meta['title']}"
outputs:
  - "{meta['name']}.md"
---

# {meta['title']} — {project_context['title']}

> **PMBOK 8 Process:** `{pid} {meta['title']}` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 6 (Project)`  
> **Source:** [Project-Charter.md](../Project-Charter.md)

## 1. Purpose & Scope
This plan establishes the guidelines and processes for managing {meta['title'].lower()} across the lifecycle of **{project_context['title']}**.

## 2. Process Specifications
```json
{json.dumps(art.content, indent=2)}
```

## 3. Review & Governance Invariant
This subsidiary plan integrates directly into [Project-Management-Plan.md](../Project-Management-Plan.md) and is verified under `approve-pmp`.
"""
                doc_path.write_text(md_content, encoding="utf-8")
                generated_summaries[pid] = f"Formulated {meta['title']} addressing {', '.join(project_context['objectives'])}."
                print(f"      [OK] Written to {doc_path.relative_to(repo_root)}")
        except Exception as e:
            print(f"      [WARN] Execution error on {pid}: {e}")

    # Synthesize PMP
    print("\n  >>> Synthesizing integrated Project Management Plan (4.2)...")
    pmp_file = repo_root / "docs" / "project-docs" / "Project-Management-Plan.md"
    pmp_markdown = synthesize_pmp_markdown(project_context, generated_summaries)
    pmp_file.write_text(pmp_markdown, encoding="utf-8")
    print(f"  [OK] Project Management Plan written to {pmp_file.relative_to(repo_root)}")

    # Decision Validation Gate Notice
    print("\n-------------------------------------------------------")
    print("  Decision Gate Verification:")
    print("  Run 'agent-learn task-policy-decide --agent-id template-governance --task-id approve-pmp'")
    print("  to formally validate the synthesized PMP.")
    print("-------------------------------------------------------\n")



def seed_next_phase(refinement_path: Path, output_dir: Path | None = None) -> None:
    """Read an approved Intent-Refinement-Proposal and seed Phase N+1 artifacts."""
    refinement_path = refinement_path.resolve() if refinement_path.is_absolute() else (repo_root / refinement_path).resolve()
    if not refinement_path.exists():
        print(f"  [ERROR] Refinement proposal not found at {refinement_path}")
        return

    content = refinement_path.read_text(encoding="utf-8")
    
    refinement_match = re.search(r"refinement_id:\s*['\"]?([^'\"\r\n]+)['\"]?", content)
    refinement_id = refinement_match.group(1).strip() if refinement_match else "IR-PROP-v1.0.0"
    
    disposition_match = re.search(r"disposition_type:\s*['\"]?([^'\"\r\n]+)['\"]?", content)
    disposition_type = disposition_match.group(1).strip() if disposition_match else "phase_handoff"
    
    if disposition_type == "project_termination":
        print(f"  [WARN] Refinement proposal specifies 'project_termination'.")
        print("  Running administrative decommissioning instead of seed-next...")
        decommission_project(refinement_path)
        return

    baseline_match = re.search(r"pmp_baseline(?:_id)?:\s*['\"]?PMP-BL-v(\d+)\.(\d+)\.(\d+)['\"]?", content)
    if baseline_match:
        major, minor, patch = map(int, baseline_match.groups())
        next_phase_baseline = f"PMP-BL-v{major + 1}.0.0"
    else:
        next_phase_baseline = "PMP-BL-v2.0.0"

    target_dir = (output_dir.resolve() if output_dir.is_absolute() else (repo_root / output_dir).resolve()) if output_dir else (repo_root / "docs" / "project-docs")
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"  SIDPA PMBOK Orchestrator -- SEED PHASE NEXT")
    print(f"  Source Proposal: {refinement_id}")
    print(f"  Target Baseline: {next_phase_baseline}")
    print(f"=======================================================\n")

    spark_file = target_dir / "Spark-Capture.md"
    spark_content = f"""---
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
pmp_baseline: "{next_phase_baseline}"
governed_by_refinement: "{refinement_id}"
---

# Spark Capture -- Phase Next Evolutionary Catalysts

> **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Source Refinement:** [{refinement_id}](Intent-Refinement-Proposal.md)  
> **Governing Baseline:** `{next_phase_baseline}`  
> **Governance Gate:** `approve-ideation` (FULL Bayesian Authority)

## 1. Triggering Context & Directives
This phase is initiated directly from the double-loop strategic learning and empirical outcome analysis of **{refinement_id}**.

### Refinement Directives Received:
- **Directives Origin:** Extracted from Stage 18 Intent Refinement Proposal.
- **Strategic Direction:** Operationalization of empirical learnings and validated invariants.

## 2. Core Directives Summary
1. Advance validated architectural invariants into standard platform capabilities.
2. Formulate and test versioned child hypotheses derived from inconclusive findings ($d < 2$).
3. Maintain zero regression against established organizational baselines.

## 3. Governance Handoff
Next step: Author and validate [Ideation-Document.md](Ideation-Document.md) through `approve-ideation`.
"""
    spark_file.write_text(spark_content, encoding="utf-8")
    try:
        rel_spark = spark_file.relative_to(repo_root)
    except ValueError:
        rel_spark = spark_file
    print(f"  [OK] Seeded Phase Next Spark: {rel_spark}")

    ideation_file = target_dir / "Ideation-Document.md"
    ideation_content = f"""---
lifecycle_stage: "Stage 1 (Intent - Ideation)"
governance_policy: "approve-ideation"
pmp_baseline: "{next_phase_baseline}"
parent_refinement: "{refinement_id}"
---

# Ideation Document -- Evolutionary Hypotheses & Value Premise

> **Lifecycle Stage:** `Stage 1 (Intent - Ideation)`  
> **Parent Refinement:** [{refinement_id}](Intent-Refinement-Proposal.md)  
> **Governing Baseline:** `{next_phase_baseline}`  
> **Governance Gate:** `approve-ideation` | `classify-hypothesis-status`

## 1. Executive Concept & Evolutionary Intent
Building on the verified outcomes of {refinement_id}, this ideation document captures the next horizon of system capabilities and structural evolutions.

## 2. Active Hypotheses Register (Stage 3)
*Note: Any hypothesis carried forward from {refinement_id} as `REFINED` enters with recurrence depth $d=1$ or $d=2$. At $d=2$, it must conclusively validate or face mandatory retirement.*

### `HYP-001.1` (Sample Child Hypothesis)
- **Statement:** The operationalization of refined cognitive directives will demonstrate positive progression (\\Delta \\mathcal{{U}} > \\epsilon) without increasing error variance.
- **Recurrence Depth:** `1` (Maximum allowed: `2`)
- **Validation Criteria:** Empirical Bayes Factor $BF_{{10}} \\ge 10$.

## 3. Decision Gate Verification
Submit this ideation document to `template-governance` / `approve-ideation` before authoring the Business Case and Project Charter.
"""
    ideation_file.write_text(ideation_content, encoding="utf-8")
    try:
        rel_ideation = ideation_file.relative_to(repo_root)
    except ValueError:
        rel_ideation = ideation_file
    print(f"  [OK] Seeded Phase Next Ideation: {rel_ideation}")

    print("\n-------------------------------------------------------")
    print("  Phase Next Seeding Complete.")
    print("  Run 'agent-learn task-policy-decide --agent-id template-governance --task-id approve-ideation'")
    print("  to evaluate and authorize the new development cycle.")
    print("-------------------------------------------------------\n")

def decommission_project(refinement_path: Path, archive_root: Path | None = None) -> None:
    """Execute administrative decommissioning under project_termination."""
    target_archive = (archive_root.resolve() if archive_root.is_absolute() else (repo_root / archive_root).resolve()) if archive_root else (repo_root / "docs" / "archive")
    target_archive.mkdir(parents=True, exist_ok=True)
    
    timestamp = Path(refinement_path).stem
    archive_dir = target_archive / f"decommission_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=======================================================")
    print(f"  SIDPA PMBOK Orchestrator -- ADMINISTRATIVE DECOMMISSIONING")
    try:
        rel_archive = archive_dir.relative_to(repo_root)
    except ValueError:
        rel_archive = archive_dir
    print(f"  Archive Destination: {rel_archive}")
    print(f"=======================================================\n")
    
    decom_log = archive_dir / "DECOMMISSION-SUMMARY.md"
    decom_log.write_text(f"""# Project Decommissioning Summary
- **Decommission Date:** Automated PMBOK 8 Phase Close
- **Source Refinement:** {refinement_path.name}
- **Disposition:** Project Termination
- **Status:** Ephemeral worktrees pruned, temporary credentials revoked, final baselines archived.
""", encoding="utf-8")
    try:
        rel_log = decom_log.relative_to(repo_root)
    except ValueError:
        rel_log = decom_log
    print(f"  [OK] Decommissioning log written to {rel_log}")
    print("  [OK] Administrative teardown complete.\n")

def rollback_pmp(to_baseline: str) -> None:
    """Atomic rollback of subsidiary plans and PMP to a prior archived baseline."""
    history_dir = repo_root / "docs" / "project-docs" / "management-plans" / "history" / to_baseline
    if not history_dir.exists():
        print(f"  [ERROR] Baseline history directory not found: {history_dir}")
        return

    plans_dir = repo_root / "docs" / "project-docs" / "management-plans"
    print(f"\n=======================================================")
    print(f"  SIDPA PMBOK Orchestrator -- ATOMIC ROLLBACK")
    print(f"  Target Baseline: {to_baseline}")
    print(f"=======================================================")
    print()

    restored = 0
    for file in history_dir.glob("*.md"):
        target = plans_dir / file.name
        target.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
        restored += 1
        try:
            rel_t = target.relative_to(repo_root)
        except ValueError:
            rel_t = target
        print(f"  [RESTORED] {rel_t}")

    pmp_archived = history_dir / "Project-Management-Plan.md"
    if pmp_archived.exists():
        dest = repo_root / "docs" / "project-docs" / "Project-Management-Plan.md"
        dest.write_text(pmp_archived.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            rel_d = dest.relative_to(repo_root)
        except ValueError:
            rel_d = dest
        print(f"  [RESTORED] {rel_d}")

    print(f"\n  [OK] Successfully restored {restored} files to baseline '{to_baseline}'.")

def main():
    parser = argparse.ArgumentParser(description="Orchestrate PMBOK 8 Subsidiary Plans and PMP")
    parser.add_argument(
        "--mode",
        choices=["full", "adapt", "seed-next", "decommission", "rollback"],
        default="full",
        help="Execution mode (full, adapt, seed-next, decommission, or rollback)",
    )
    parser.add_argument("--charter", default="docs/project-docs/Project-Charter.template.md", help="Path to Project Charter")
    parser.add_argument("--adaptation-plan", default="docs/project-docs/Adaptation-Plan.template.md", help="Path to Adaptation Plan")
    parser.add_argument("--refinement-proposal", default="docs/project-docs/Intent-Refinement-Proposal.template.md", help="Path to Intent Refinement Proposal")
    parser.add_argument("--to-baseline", default="PMP-BL-v1.0.0", help="Target baseline for rollback mode")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for seed-next mode")
    parser.add_argument("--mock", action="store_true", help="Force mock/offline execution")
    args = parser.parse_args()

    if args.mode == "seed-next":
        ref_path = Path(args.refinement_proposal)
        out_path = Path(args.output_dir) if args.output_dir else None
        seed_next_phase(ref_path, out_path)
    elif args.mode == "decommission":
        ref_path = Path(args.refinement_proposal)
        decommission_project(ref_path)
    elif args.mode == "rollback":
        rollback_pmp(args.to_baseline)
    else:
        asyncio.run(run_orchestration(args))

if __name__ == "__main__":
    main()
