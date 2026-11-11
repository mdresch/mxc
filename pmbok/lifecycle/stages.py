"""Unified 18-stage lifecycle registry.

Numbers match ``docs/chain-coverage.md`` §2 in sidpa-template ``0e88dd0``
(11 Nov 2026). ``validator.py`` enforces:

  * Stage 4 benefit documents before an approved Stage 2 Charter.
  * Stage 6 requirements before a Stage 7 PMP baseline.
  * Stage 7 PMP elaborated to ``PMP-BL-v1.1.0`` or later before Stage 9/10
    canonical execution evidence.
  * Stage 18 loop closure back to Stage 1 (refinesIntent) and/or an ADR.
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
    Stage(1, "Intent: Spark & Ideation", 1, ("00",),
          ("Spark-Capture*.md", "Ideation-Document*.md"),
          "approve-ideation", "Initiating: Strategic Need Identification",
          ("docs/project-docs",)),
    Stage(2, "Objective: Project Charter", 1, ("05",),
          ("Project-Charter*.md",),
          "approve-charter", "Initiating: 4.1 Develop Project Charter",
          ("docs/project-docs",)),
    Stage(3, "Hypothesis", 1, ("00",),
          ("HYP-*.md", "Ideation-Document*.md"),
          "classify-hypothesis-status", "Initiating: Design Assumption Formulation",
          ("docs/project-docs",)),
    Stage(4, "Benefit: Business Case & Benefits Statement", 1, ("05",),
          ("Business-Case*.md", "Benefits-Statement*.md", "Stakeholder-Register*.md"),
          "approve-business-case", "Initiating: Business Case & Benefits Planning",
          ("docs/project-docs",)),
    Stage(5, "Pillars & Architecture", 1, ("01",),
          ("PILLARS-EXERCISE.md", "PILLARS*.md"),
          "approve-adr", "Planning: Architectural Strategy Formulation",
          ("docs/07-architecture",)),
    Stage(6, "Requirement: ADR, BRD, FDD, User Stories", 2, ("01", "02", "03", "04"),
          ("ADR-*.md", "BRD-*.md", "FDD-*.md", "epic-*.md", "EPIC-*.md"),
          "approve-adr", "Planning: 5.2 Collect Requirements & 5.3 Define Scope",
          ("docs/07-architecture", "docs/project-docs/Business-Requirements",
           "docs/project-docs/Functional-Design", "docs/user-stories")),
    Stage(7, "Project: PMP & Subsidiary Plans", 2, ("05",),
          ("Project-Management-Plan*.md", "*-Management-Plan*.md", "*-Engagement-Plan*.md"),
          "approve-pmp", "Planning: 4.2 Develop Project Management Plan",
          ("docs/project-docs", "docs/project-docs/management-plans")),
    Stage(8, "Implementation Readiness", 2, ("04.5",),
          ("Stage-8-Implementation-Authorization-Notice.md",),
          "validate-intent-foundation", "Planning to Executing: Implementation Authorization",
          ("docs/project-docs/Status-Reports",)),
    Stage(9, "Deliverable", 2, ("04.5",),
          ("Plan-*.md",),
          "implement-story", "Executing: 4.3 Direct & Manage Project Work"),
    Stage(10, "Verification Evidence", 3, ("07",),
          ("*.contract.test.*", "ContractTest-*.md"),
          "contract-test-suite", "Monitoring & Controlling: 8.3 Control Quality"),
    Stage(11, "Audit Record", 3, ("07",),
          ("Audit-Register.md", "Audit-Finding.md"),
          "approve-audit-record", "Monitoring & Controlling: 8.2 Manage Quality Audits",
          ("docs/registers",)),
    Stage(12, "Actual Outcome", 3, ("08",),
          ("OUTCOME-*.md", "AFFECT-*.md"),
          "empirical-observation", "Monitoring & Controlling: 5.5 Validate Scope"),
    Stage(13, "Observation", 3, ("08",),
          ("OBS-*.md",),
          "ingest-telemetry-signal", "Monitoring & Controlling: 4.5 Monitor & Control"),
    Stage(14, "Insight", 3, ("06",),
          ("INSIGHT-*.md",),
          "resolve-kb-conflict", "Monitoring & Controlling: 4.4 Manage Project Knowledge"),
    Stage(15, "Lesson Learned", 4, ("06",),
          ("LL-*.md", "Lesson-*.md"),
          "resolve-kb-conflict", "Monitoring & Controlling: 4.4 Lessons Learned"),
    Stage(16, "Governance Change", 4, ("09",),
          ("GC-*.md",),
          "classify-diff-type", "Monitoring & Controlling: 4.6 Integrated Change Control",
          ("docs/project-docs",)),
    Stage(17, "Adaptation Plan", 4, ("05",),
          ("Adaptation-Plan.md", "ADAPT-*.md"),
          "approve-adaptation-plan", "Closing: Tailoring",
          ("docs/project-docs",)),
    Stage(18, "Intent Refinement", 4, ("05",),
          ("Intent-Refinement-Proposal.md",),
          "approve-intent-refinement", "Closing: 4.7 Close Project or Phase",
          ("docs/project-docs",)),
)

# Sibling policies for a stage whose registry slot holds only one policy id.
EXTRA_POLICIES: tuple[str, ...] = (
    "approve-brd",
    "approve-fdd",
    "approve-user-stories",
    "approve-subsidiary-plan",
    "escalate-diff-response",
)

# Ordering invariants (documented here, enforced in validator.py).
INVARIANTS: dict[str, str] = {
    "I1": "Stage 4 business documents are approved before an approved Stage 2 Project Charter.",
    "I2": "Stage 6 requirements exist, and the Stage 7 PMP is at PMP-BL-v1.1.0 or later, "
          "before Stage 9/10 canonical execution evidence.",
    "I3": "Every stage policy has a governing policy shape in docs/policy-shapes.",
    "I4": "An approved or concretely identified Stage 18 Intent-Refinement-Proposal closes "
          "the loop through lineage.root_spark, a Phase N+1 spark catalyst, or "
          "refinesIntent/amendsADR. A Stage 16 design-time GC-* record and a Stage 17 "
          "adaptation record do not refine intent.",
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

