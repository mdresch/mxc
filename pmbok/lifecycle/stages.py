"""Unified 18-stage lifecycle registry (single source of truth).

Mirrors the Second Brain "Software Engineering Lifecycle Pipeline" and the
SIDPA closed-loop lifecycle. Everything that needs to know "what are the
stages, which folder, which artifact, which policy" reads it from here.

Ordering rules encoded elsewhere (see validator.py):
  * Stage 3 (Business Case, Benefits Statement, Stakeholder Register)
    precedes Stage 4 (Project Charter).
  * The PMP is progressively elaborated: a draft baseline exists after the
    Charter, and is re-elaborated and locked at Stage 10 (after User Stories)
    before Stage 11 (agent execution) and Stage 12 (contract tests).
  * Stage 18 closes the loop back to Stage 1 (refinesIntent) and Stage 5
    (amendsADR).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Canonical numbered folders, relative to the lifecycle root (docs/lifecycle).
FOLDERS: dict[str, str] = {
    "00": "00-intent-charter",
    "01": "01-architecture-decisions",
    "02": "02-business-requirements",
    "03": "03-functional-design",
    "03.5": "03.5-technical-design",
    "04": "04-user-stories-epics",
    "04.5": "04.5-agent-execution-plans",
    "05": "05-project-governance-plans",
    "06": "06-synthesis-lessons-learned",
    "07": "07-contract-tests-quality-gates",
    "07.5": "07.5-agent-skills-tooling",
    "08": "08-project-telemetry-dashboard",
    "09": "09-ai-governance-reasoning",
}

PHASES: dict[int, str] = {
    1: "Inception, Concept Research & Architecture Decisions",
    2: "Specification, User Stories, Management Plans & Agent Skills",
    3: "Contracts, Runtime Telemetry & Empirical Observation",
    4: "Cognitive Synthesis, Adaptation & Closed-Loop Evolution",
}


@dataclass(frozen=True)
class Stage:
    number: int
    name: str
    phase: int
    folder_keys: tuple[str, ...]  # keys into FOLDERS
    artifact_globs: tuple[str, ...]  # filename globs that evidence the stage
    policy: str  # governing TaskPolicy id
    pmbok: str  # PMBOK 8 process group / process
    legacy_paths: tuple[str, ...] = field(default_factory=tuple)  # pre-unification locations

    @property
    def folders(self) -> tuple[str, ...]:
        return tuple(FOLDERS[k] for k in self.folder_keys)


STAGES: tuple[Stage, ...] = (
    Stage(1, "Strategic Intent, Spark & Ideation", 1, ("00",),
          ("Spark-Capture*.md", "Ideation-Document*.md", "INTENT-*.md"),
          "approve-ideation", "Initiating: Strategic Need Identification",
          ("docs/project-docs",)),
    Stage(2, "Feature Research & Cybernetic Information Flow Loop", 1, ("06",),
          ("Concept-*.md", "Cybernetic-Flow-Loop-*.md"),
          "score-concept-authority", "Initiating: Domain Grounding & Gap Discovery"),
    Stage(3, "Business Case, Benefits Statement & Stakeholder Register", 1, ("05",),
          ("Business-Case*.md", "Benefits-Statement*.md", "Stakeholder-Register*.md"),
          "approve-business-case", "Initiating: Business Case & Benefits Planning",
          ("docs/project-docs",)),
    Stage(4, "Project Charter & Architectural Hypothesis", 1, ("05",),
          ("Project-Charter*.md", "HYP-*.md"),
          "approve-charter", "Initiating: 4.1 Develop Project Charter",
          ("docs/project-docs",)),
    Stage(5, "Architecture Decision Record (ADR)", 1, ("01",),
          ("ADR-*.md",), "approve-adr", "Planning: Architecture Governance",
          ("docs/07-architecture",)),
    Stage(6, "Business Requirements (BRD)", 2, ("02",),
          ("BRD-*.md",), "approve-brd", "Planning: 5.2 Collect Requirements",
          ("docs/project-docs/Business-Requirements",)),
    Stage(7, "Functional Design Document (FDD)", 2, ("03",),
          ("FDD-*.md",), "approve-fdd", "Planning: 5.3 Define Scope",
          ("docs/project-docs/Functional-Design",)),
    Stage(8, "Technical Design Spec (TDS)", 2, ("03.5",),
          ("TDS-*.md",), "approve-tds", "Planning: Component Architecture & DDL"),
    Stage(9, "User Stories & Delivery Slices", 2, ("04",),
          ("EPIC-*.md", "epic-*.md", "Story-*.md", "story-*.md"),
          "approve-user-stories", "Planning: 5.4 Create WBS & Backlog",
          ("docs/user-stories",)),
    Stage(10, "Management Plans & PMP Update (Progressive Elaboration)", 2, ("05",),
          ("Project-Management-Plan*.md", "*-Management-Plan*.md", "*-Engagement-Plan*.md"),
          "approve-pmp", "Planning: 4.2 Develop Project Management Plan",
          ("docs/project-docs/management-plans", "docs/project-docs")),
    Stage(11, "Agent Skills & Execution Plan", 2, ("04.5", "07.5"),
          ("Plan-*.md", "SKILL.md", "Skill-*.md"),
          "validate-intent-foundation", "Executing: 4.3 Direct & Manage Work",
          (".claude/skills",)),
    Stage(12, "Executable Contract Tests & Gates", 3, ("07",),
          ("*.contract.test.*", "test_*.py", "ContractTest-*.md", "Audit-Register*.md"),
          "approve-audit-record", "Monitoring & Controlling: 8.3 Control Quality",
          ("tests", "docs/registers")),
    Stage(13, "Telemetry Observation (OBS)", 3, ("08",),
          ("OBS-*.md",), "ingest-telemetry-signal",
          "Monitoring & Controlling: 4.5 Monitor & Control"),
    Stage(14, "Empirical Outcome & Affect Measurement", 3, ("08",),
          ("OUTCOME-*.md", "AFFECT-*.md"), "evaluate-outcome-delta",
          "Monitoring & Controlling: 5.5 Validate Scope"),
    Stage(15, "Diagnostic Finding & Insight", 3, ("06",),
          ("INSIGHT-*.md",), "resolve-kb-conflict",
          "Monitoring & Controlling: 4.4 Manage Knowledge"),
    Stage(16, "Crystallized Lesson Learned", 4, ("06",),
          ("LL-*.md",), "codify-lesson-learned",
          "Monitoring & Controlling: 4.4 Lessons Learned"),
    Stage(17, "AI Reasoning & Recommendation Trace", 4, ("09",),
          ("AIR-*.md", "AIREC-*.md"), "evaluate-ai-recommendation",
          "Monitoring & Controlling: AI Governance"),
    Stage(18, "Governance Change, Adaptation & Intent Refinement", 4, ("05",),
          ("GC-*.md", "ADAPT-*.md", "Adaptation-Plan*.md", "Intent-Refinement-Proposal*.md"),
          "classify-diff-type", "Closing: 4.6 Integrated Change & Tailoring",
          ("docs/project-docs",)),
)

# Policies that the stage registry requires. Stages 18 additionally uses
# approve-intent-refinement; stage 3 uses classify-hypothesis-status for HYP-*.
EXTRA_POLICIES: tuple[str, ...] = (
    "approve-subsidiary-plan",
    "approve-intent-refinement",
    "classify-hypothesis-status",
    "approve-adaptation-plan",
    "escalate-diff-response",
)

# Ordering invariants (documented here, enforced in validator.py).
INVARIANTS: dict[str, str] = {
    "I1": "Stage 3 business documents are approved before the Stage 4 Project Charter.",
    "I2": "PMP is progressively elaborated and locked (PMP-BL-vX.Y.Z, Y>=1) at Stage 10 "
          "before Stage 11 execution plans or Stage 12 contract tests exist.",
    "I3": "Every stage artifact must have a governing policy shape in docs/policy-shapes.",
    "I4": "Stage 18 closes the loop: a governance change/adaptation must refine intent "
          "(Stage 1) and/or amend an ADR (Stage 5).",
}


def stage(number: int) -> Stage:
    return STAGES[number - 1]


def required_policies() -> list[str]:
    seen: list[str] = []
    for s in STAGES:
        if s.policy not in seen:
            seen.append(s.policy)
    for p in EXTRA_POLICIES:
        if p not in seen:
            seen.append(p)
    return seen

