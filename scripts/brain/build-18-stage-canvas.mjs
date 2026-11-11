import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { resolveVaultRoot, resolveWikiRoot } from './vault-resolver.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vaultRoot = resolveVaultRoot();
const wikiRoot = resolveWikiRoot(vaultRoot);
const targetCanvasPath = path.join(wikiRoot, '18-Stage-Closed-Loop-Lifecycle.canvas');

console.log('Building 18-Stage Closed-Loop Lifecycle Canvas at:', targetCanvasPath);

const nodes = [
  // Master Header
  {
    id: "node-header",
    type: "text",
    text: "# 🔄 18-Stage Closed-Loop Cognition & Adaptation Lifecycle\n### *Unbroken End-to-End Traceability: From Strategic Intent to Emergent Institutional Capability*\n\n- **Governing Architecture**: 18 Governed Stages, 3 Serpentine Phases, 19-Step Closed Cybernetic Loop.\n- **Enterprise Ontologies**: PMI-PMBOK 7th/8th Ed., IIBA-BABOK v3, DAMA-DMBOK2, W3C PROV-O, and `ONTOLOGY.json` (v1.1.0-LOCKED).\n- **Cybernetic Law**: Every strategic intent flows deterministically through hypotheses, requirements, and execution deliverables, while runtime telemetry, developer affect, and diagnostic lessons close the loop through institutional adaptations and intent refinement.\n- **Return Semantics**: Stage 18 (`Emergent Capability`) and Stage 16 (`Governance Change`) loop back into Stage 1 (`Intent`) via `refinesIntent` (Step 19), eliminating organizational drift and amnesia.",
    x: 0,
    y: -740,
    width: 3160,
    height: 250,
    color: "6" // Purple
  },

  // ==========================================
  // PHASE 1: STRATEGIC INTENT, VALUE & SCOPING (STAGES 1-6)
  // ==========================================
  {
    id: "group-phase-1",
    type: "group",
    label: "PHASE 1: STRATEGIC INTENT, VALUE PROPOSITION & GOVERNANCE SCOPING (FORWARD FLOW ➔)",
    x: 0,
    y: -440,
    width: 3160,
    height: 390,
    color: "6"
  },
  {
    id: "node-stage-1",
    type: "text",
    text: "### 💡 1. Strategic Intent\n**Ontology Class**: `pmClass: Intent`  \n**Node Type**: `intent`  \n**Location**: `00 Intent & Charter/`  \n**ID Pattern**: `INTENT-{nnnn}`  \n\n- **Semantic Definition**: Originating purpose, motivation, or strategic imperative (The \"Why\").\n- **Input**: Executive vision, stakeholder mandate, market shift, or telemetry alert.\n- **Exit Gate**: Formally articulated strategic intent with target value proposition.\n- **Traceability Link**: `initiates` ➔ Objective.",
    x: 40,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },
  {
    id: "node-stage-2",
    type: "text",
    text: "### 🎯 2. Strategic Objective\n**Ontology Class**: `pmClass: Objective`  \n**Node Type**: `objective`  \n**Location**: `00 Intent & Charter/`  \n**ID Pattern**: `OBJ-{nnnn}`  \n\n- **Semantic Definition**: Measurable operational or architectural goal advancing the intent.\n- **Input**: Approved strategic intent, corporate roadmaps, OKRs/KPIs.\n- **Exit Gate**: SMART criteria with quantified target metrics and time horizons.\n- **Traceability Link**: `supportsIntent` ➔ Intent; informs Hypothesis.",
    x: 560,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },
  {
    id: "node-stage-3",
    type: "text",
    text: "### 🔬 3. Architectural Hypothesis\n**Ontology Class**: `pmClass: Hypothesis`  \n**Node Type**: `hypothesis`  \n**Location**: `01 Architecture Decisions (ADR)/`  \n**ID Pattern**: `HYP-{nnnn}`  \n\n- **Semantic Definition**: Falsifiable proposition, design assumption, or value premise.\n- **Input**: Strategic objective, trade-off analysis, concept grounding.\n- **Exit Gate**: Explicit falsification criteria (`falsificationCriteria`) & testing strategy.\n- **Traceability Link**: `basedOnHypothesis` ➔ Benefit & ADR.",
    x: 1080,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },
  {
    id: "node-stage-4",
    type: "text",
    text: "### 📈 4. Expected Benefit\n**Ontology Class**: `pmClass: Benefit`  \n**Node Type**: `benefit`  \n**Location**: `00 Intent & Charter/`  \n**ID Pattern**: `BENEFIT-{nnnn}`  \n\n- **Semantic Definition**: Quantifiable positive outcome and business return justifying cost.\n- **Input**: Formulated hypothesis, financial models, user impact projections.\n- **Exit Gate**: Approved commercial ROI, latency reduction, or efficiency threshold.\n- **Traceability Link**: `enabledByCapability` ➔ Capability Baseline.",
    x: 1600,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },
  {
    id: "node-stage-5",
    type: "text",
    text: "### 🏛️ 5. Capability Baseline\n**Ontology Class**: `pmClass: Capability`  \n**Node Type**: `capability`  \n**Location**: `05 Project Governance & Plans/`  \n**ID Pattern**: `CAP-{nnnn}`  \n\n- **Semantic Definition**: Baseline institutional or systemic competency required for delivery.\n- **Input**: Technical skill assessment, infrastructure maturity, team capabilities.\n- **Exit Gate**: Maturity readiness check (`Emergent` ➔ `Operational`); gap analysis.\n- **Traceability Link**: `implements` ➔ Project Scope.",
    x: 2120,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },
  {
    id: "node-stage-6",
    type: "text",
    text: "### 📦 6. Project & Governance Scope\n**Ontology Class**: `pmClass: Project`  \n**Node Type**: `governance`  \n**Location**: `05 Project Governance & Plans/`  \n**ID Pattern**: `Project-Charter`  \n\n- **Semantic Definition**: Governed temporary endeavor binding scope, budget, and teams.\n- **Input**: Strategic charter, sponsor authorization, baseline capabilities.\n- **Exit Gate**: Formally chartered governance boundary, sponsor sign-off, lead architect assignment.\n- **Traceability Link**: `contains` ➔ Requirement.",
    x: 2640,
    y: -380,
    width: 450,
    height: 300,
    color: "6"
  },

  // ==========================================
  // PHASE 2: SPECIFICATION, DELIVERY & QUALITY GATES (STAGES 7-12)
  // ==========================================
  {
    id: "group-phase-2",
    type: "group",
    label: "PHASE 2: SPECIFICATION, WORK PACKAGES, DELIVERY & QUALITY GATES (SNAKE FLOW ➔)",
    x: 0,
    y: -10,
    width: 3160,
    height: 390,
    color: "5"
  },
  {
    id: "node-stage-7",
    type: "text",
    text: "### 📋 7. Requirements & Specifications\n**Ontology Class**: `pmClass: Requirement` / `TechnicalDesign`  \n**Node Type**: `brd` / `fdd` / `tds`  \n**Location**: `02 BRD/`, `03 FDD/`, `03.5 TDS/`  \n**ID Pattern**: `BRD-{nnnn}` / `FDD-{nnnn}` / `TDS-{nnnn}`  \n\n- **Semantic Definition**: Formal condition or capability bridging business rules to schemas.\n- **Input**: Project charter, accepted ADRs, stakeholder user journeys.\n- **Exit Gate**: Schema validation, interface contracts, error cascade specifications.\n- **Traceability Link**: `tracedTo` ➔ Work Package.",
    x: 2640,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },
  {
    id: "node-stage-8",
    type: "text",
    text: "### 🧩 8. Work Package & Slicing\n**Ontology Class**: `pmClass: WorkPackage`  \n**Node Type**: `epic` / `implementation_plan`  \n**Location**: `04 User Stories & Epics/`, `04.5 Plans/`  \n**ID Pattern**: `Epic-{n}` / `PLAN-{nnnn}`  \n\n- **Semantic Definition**: Deliverable-oriented decomposition of engineering activities.\n- **Input**: Approved TDS/FDD, architectural invariants, dependency graphs.\n- **Exit Gate**: INVEST-sliced user stories, acceptance criteria, execution sequence.\n- **Traceability Link**: `produces` ➔ Deliverable.",
    x: 2120,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },
  {
    id: "node-stage-9",
    type: "text",
    text: "### ⚙️ 9. Deliverable & Invariant Code\n**Ontology Class**: `pmClass: Deliverable`  \n**Node Type**: `story` / `adr` / `skill`  \n**Location**: `04 Stories/`, `01 ADR/`, `07.5 Skills/`  \n**ID Pattern**: `Story {x.y}` / `ADR-{nnnn}` / `SKILL.md`  \n\n- **Semantic Definition**: Concrete tangible output produced by human engineers or AI agents.\n- **Input**: Sliced work packages, agent competencies, code scaffolding.\n- **Exit Gate**: Peer review, ADR compliance, clean build, automated lint pass.\n- **Traceability Link**: `verifiedBy` ➔ Verification Evidence.",
    x: 1600,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },
  {
    id: "node-stage-10",
    type: "text",
    text: "### 📜 10. Verification Evidence\n**Ontology Class**: `pmClass: Evidence`  \n**Node Type**: `contract_test` / `walkthrough`  \n**Location**: `07 Contract Tests/`, `06.5 Walkthroughs/`  \n**ID Pattern**: `*.contract.test.ts` / `WALKTHROUGH-{nnnn}`  \n\n- **Semantic Definition**: Empirical verification artifact proving invariant correctness.\n- **Input**: Executable code, contract test runner, implementation assertions.\n- **Exit Gate**: 100% passing test assertion score, zero unapproved schema drift.\n- **Traceability Link**: `evaluates` ➔ Audit Record.",
    x: 1080,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },
  {
    id: "node-stage-11",
    type: "text",
    text: "### ⚖️ 11. Governance Audit & Gate\n**Ontology Class**: `pmClass: Audit` / `QualityGate`  \n**Node Type**: `audit`  \n**Location**: `05 Project Governance & Plans/`  \n**ID Pattern**: `AUDIT-{nnnn}` / `QualityGate`  \n\n- **Semantic Definition**: Formal review verifying compliance, security, and quality.\n- **Input**: Verification evidence, contract test logs, security scan results.\n- **Exit Gate**: `compile-ontology-graph.mjs` reports 100% Graph Health Score; gate signed off.\n- **Traceability Link**: `evaluatesOutcome` ➔ Actual Outcome.",
    x: 560,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },
  {
    id: "node-stage-12",
    type: "text",
    text: "### 📊 12. Actual Outcome & Affect\n**Ontology Class**: `pmClass: Outcome` / `Metric`  \n**Node Type**: `outcome` / `affect_measurement`  \n**Location**: `08 Project Telemetry Dashboard/`  \n**ID Pattern**: `OUTCOME-{nnnn}` / `AFFECT-{nnnn}`  \n\n- **Semantic Definition**: Realized operational impact and developer affective vitality (PANAS).\n- **Input**: Production telemetry, latency histograms, error rates, cognitive friction surveys.\n- **Exit Gate**: `validatesHypothesis` evaluated against originating `HYP-nnnn` baseline.\n- **Traceability Link**: `generatesObservation` ➔ Observation.",
    x: 40,
    y: 50,
    width: 450,
    height: 300,
    color: "5"
  },

  // ==========================================
  // PHASE 3: TELEMETRY, SYNTHESIS & CYBERNETIC ADAPTATION (STAGES 13-18)
  // ==========================================
  {
    id: "group-phase-3",
    type: "group",
    label: "PHASE 3: TELEMETRY, COGNITIVE SYNTHESIS & CYBERNETIC ADAPTATION (FORWARD FLOW ➔)",
    x: 0,
    y: 420,
    width: 3160,
    height: 390,
    color: "4"
  },
  {
    id: "node-stage-13",
    type: "text",
    text: "### 📡 13. Telemetry Observation\n**Ontology Class**: `pmClass: Observation`  \n**Node Type**: `observation`  \n**Location**: `raw/observations/` & `06 Synthesis/`  \n**ID Pattern**: `OBS-{nnnn}`  \n\n- **Semantic Definition**: Empirical data point, anomaly, or raw event detected in runtime or test streams.\n- **Input**: OpenTelemetry traces, Prometheus metrics, runtime exceptions, regression signals.\n- **Exit Gate**: Triaged observation linked to source deliverable and architecture decision.\n- **Traceability Link**: `yieldsInsight` ➔ Insight.",
    x: 40,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },
  {
    id: "node-stage-14",
    type: "text",
    text: "### 💡 14. Diagnostic Insight\n**Ontology Class**: `pmClass: Insight`  \n**Node Type**: `insight`  \n**Location**: `raw/insights/` & `06 Synthesis/`  \n**ID Pattern**: `INSIGHT-{nnnn}`  \n\n- **Semantic Definition**: Diagnostic discovery or recognized causal pattern synthesized from observations.\n- **Input**: Correlated observations, 5-Whys root-cause analysis, failure retrospectives.\n- **Exit Gate**: Root-cause verified; status transitions `Synthesized` ➔ `Active` ➔ `Codified`.\n- **Traceability Link**: `crystallizesLesson` ➔ Lesson Learned.",
    x: 560,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },
  {
    id: "node-stage-15",
    type: "text",
    text: "### 🎓 15. Crystallized Lesson Learned\n**Ontology Class**: `pmClass: GovernanceArtifact` (`KnowledgeAsset`)  \n**Node Type**: `lesson_learned`  \n**Location**: `06 Synthesis & Lessons Learned/`  \n**ID Pattern**: `Lesson-{nnnn}`  \n\n- **Semantic Definition**: Formalized, immutable organizational knowledge preventing amnesia.\n- **Input**: Validated diagnostic insights, retrospective findings, AI reasoning analyses (`AIR-nnnn`).\n- **Exit Gate**: Codified into living agent prompts, design rules, and architectural invariants.\n- **Traceability Link**: `triggersGovernanceChange` ➔ Governance Change.",
    x: 1080,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },
  {
    id: "node-stage-16",
    type: "text",
    text: "### 📜 16. Governance Change\n**Ontology Class**: `pmClass: GovernanceChange`  \n**Node Type**: `governance_change`  \n**Location**: `05 Project Governance & Plans/`  \n**ID Pattern**: `GOV-CHG-{nnnn}`  \n\n- **Semantic Definition**: Formal institutional policy amendment, contract update, or baseline revision.\n- **Input**: Formalized lessons learned, compliance shifts, human sponsor decisions.\n- **Exit Gate**: Ratified governance policy (`Adopted`); triggers baseline update.\n- **Traceability Link**: `enables` ➔ Adaptation; fast-path `amends_adr`.",
    x: 1600,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },
  {
    id: "node-stage-17",
    type: "text",
    text: "### 🔄 17. Behavioral Adaptation\n**Ontology Class**: `pmClass: Adaptation`  \n**Node Type**: `adaptation`  \n**Location**: `06 Synthesis & Lessons Learned/`  \n**ID Pattern**: `ADAPT-{nnnn}`  \n\n- **Semantic Definition**: Empirical shift in human engineer habits or autonomous agent swarm workflows.\n- **Input**: Adopted governance change, updated agent tool definitions, new execution guidelines.\n- **Exit Gate**: Quantifiable behavioral delta (`behavioralDelta`) and high compliance rate confirmed.\n- **Traceability Link**: `crystallizesCapability` ➔ Emergent Capability.",
    x: 2120,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },
  {
    id: "node-stage-18",
    type: "text",
    text: "### 🚀 18. Emergent Capability\n**Ontology Class**: `pmClass: Capability`  \n**Node Type**: `capability`  \n**Location**: `05 Project Governance & Plans/`  \n**ID Pattern**: `CAP-{nnnn}`  \n\n- **Semantic Definition**: Institutionalized systemic competency crystallized from proven adaptations.\n- **Input**: Stabilized behavioral adaptations, validated performance uplift, mature agent skills.\n- **Exit Gate**: Capability status moves `Emergent` ➔ `Operational` ➔ `Mature`.\n- **Traceability Link**: `refinesIntent` (Step 19) ➔ Strategic Intent (Stage 1) [CLOSES LOOP].",
    x: 2640,
    y: 480,
    width: 450,
    height: 300,
    color: "4"
  },

  // ==========================================
  // SIDEBAR: CYBERNETIC INVARIANTS & MULTI-FRAMEWORK MAP
  // ==========================================
  {
    id: "group-sidebar",
    type: "group",
    label: "CYBERNETIC PRINCIPLES, GOVERNANCE INVARIANTS & TAXONOMIES",
    x: 3240,
    y: -440,
    width: 680,
    height: 1250,
    color: "2"
  },
  {
    id: "side-principles",
    type: "text",
    text: "## 🛡️ Double-Loop Cybernetic Control\n\nTraditional engineering pipelines terminate at deployment, running **open-loop** and leaking architectural intent into entropy.\n\nThe Second Brain enforces a **closed cybernetic loop**:\n1. **First-Loop Feedback (Operational)**: Real-time telemetry (`OBS-nnnn`) compares against contract assertions (`*.contract.test.ts`) to halt regressions instantly.\n2. **Second-Loop Feedback (Epistemic)**: Empirical outcomes (`OUTCOME-nnnn`) evaluate originating hypotheses (`HYP-nnnn`), while diagnostic insights (`INSIGHT-nnnn`) mandate formal governance changes (`GOV-CHG-nnnn`) that reshape future strategic intent (`INTENT-nnnn`).\n\n**Result**: Zero institutional amnesia, self-healing knowledge graph, and guaranteed convergence.",
    x: 3280,
    y: -380,
    width: 600,
    height: 270,
    color: "2"
  },
  {
    id: "side-traceability",
    type: "text",
    text: "## 💎 19-Step Traceability Invariant\n\nEvery artifact in the vault must trace seamlessly up and down the complete 19-step closed-loop sequence:\n\n`Intent` ➔ `Objective` ➔ `Hypothesis` ➔ `Benefit` ➔ `Capability` ➔ `Project` ➔ `Requirement` ➔ `Work Package` ➔ `Deliverable` ➔ `Verification Evidence` ➔ `Audit Record` ➔ `Actual Outcome` ➔ `Observation` ➔ `Insight` ➔ `Lesson Learned` ➔ `Governance Change` ➔ `Adaptation` ➔ `Emergent Capability` ➔ `Intent Refinement`\n\nAn orphaned user story without an ADR is rejected by `compile-ontology-graph.mjs`. An ADR without an empirical outcome remains flagged as unvalidated.",
    x: 3280,
    y: -80,
    width: 600,
    height: 270,
    color: "3"
  },
  {
    id: "side-affect",
    type: "text",
    text: "## 🧠 Cognitive Ergonomics & Human Affect\n\nSystem architecture is an extension of human and agent cognition:\n\n- **PANAS Measurement**: Captures developer positive/negative affect, cognitive friction, and flow state (`AFFECT-nnnn`).\n- **Cognitive Load Compression**: The structured knowledge graph compresses hop distance by **60%** and cuts feature inquiry latency from 2,700s to 314s (**8.6x speedup**).\n- **Anti-Burnout Invariant**: High cognitive friction triggers automatic prompt refinements or dedicated agent skill generation (`SKILL.md`).",
    x: 3280,
    y: 220,
    width: 600,
    height: 270,
    color: "4"
  },
  {
    id: "side-nav",
    type: "text",
    text: "## 🧭 Key Navigation Hubs & Compilers\n\n- **Software Engineering Pipeline Canvas**: [[wiki/Software-Engineering-Lifecycle-Pipeline.canvas|Software-Engineering-Lifecycle-Pipeline.canvas]]\n- **Governance Telemetry Cockpit Canvas**: [[wiki/Governance-Telemetry-Cockpit.canvas|Governance-Telemetry-Cockpit.canvas]]\n- **Interactive Simulator**: [[wiki/System/Information-Flow-Loop-Simulator.md|Information-Flow-Loop-Simulator.md]]\n- **Ontology Metamodel**: [[ONTOLOGY.json|ONTOLOGY.json (v1.1.0-LOCKED)]]\n- **Project Management Ontology**: [[PROJECT-MANAGEMENT-ONTOLOGY.json|PROJECT-MANAGEMENT-ONTOLOGY.json]]\n- **Master Traceability Matrix**: [[wiki/_MOCs/MOC - Complete Traceability Matrix (ADR - BRD - FDD - Story)|MOC - Complete Traceability Matrix]]",
    x: 3280,
    y: 520,
    width: 600,
    height: 270,
    color: "5"
  }
];

const edges = [
  // Phase 1 Forward Chain: 1 -> 2 -> 3 -> 4 -> 5 -> 6
  {
    id: "edge-1-2",
    fromNode: "node-stage-1",
    fromSide: "right",
    toNode: "node-stage-2",
    toSide: "left",
    label: "1. initiates"
  },
  {
    id: "edge-2-3",
    fromNode: "node-stage-2",
    fromSide: "right",
    toNode: "node-stage-3",
    toSide: "left",
    label: "2. informsHypothesis"
  },
  {
    id: "edge-3-4",
    fromNode: "node-stage-3",
    fromSide: "right",
    toNode: "node-stage-4",
    toSide: "left",
    label: "3. basedOnHypothesis"
  },
  {
    id: "edge-4-5",
    fromNode: "node-stage-4",
    fromSide: "right",
    toNode: "node-stage-5",
    toSide: "left",
    label: "4. enabledByCapability"
  },
  {
    id: "edge-5-6",
    fromNode: "node-stage-5",
    fromSide: "right",
    toNode: "node-stage-6",
    toSide: "left",
    label: "5. implements"
  },

  // Transition Phase 1 -> Phase 2: 6 -> 7
  {
    id: "edge-6-7",
    fromNode: "node-stage-6",
    fromSide: "bottom",
    toNode: "node-stage-7",
    toSide: "top",
    label: "6. contains (Scope Boundary)"
  },

  // Phase 2 Reverse Snake Chain: 7 -> 8 -> 9 -> 10 -> 11 -> 12
  {
    id: "edge-7-8",
    fromNode: "node-stage-7",
    fromSide: "left",
    toNode: "node-stage-8",
    toSide: "right",
    label: "7. tracedTo (INVEST Slicing)"
  },
  {
    id: "edge-8-9",
    fromNode: "node-stage-8",
    fromSide: "left",
    toNode: "node-stage-9",
    toSide: "right",
    label: "8. produces (Implementation)"
  },
  {
    id: "edge-9-10",
    fromNode: "node-stage-9",
    fromSide: "left",
    toNode: "node-stage-10",
    toSide: "right",
    label: "9. verifiedBy (Contract Invariants)"
  },
  {
    id: "edge-10-11",
    fromNode: "node-stage-10",
    fromSide: "left",
    toNode: "node-stage-11",
    toSide: "right",
    label: "10. evaluates (Quality Gates)"
  },
  {
    id: "edge-11-12",
    fromNode: "node-stage-11",
    fromSide: "left",
    toNode: "node-stage-12",
    toSide: "right",
    label: "11. evaluatesOutcome"
  },

  // Transition Phase 2 -> Phase 3: 12 -> 13
  {
    id: "edge-12-13",
    fromNode: "node-stage-12",
    fromSide: "bottom",
    toNode: "node-stage-13",
    toSide: "top",
    label: "12. generatesObservation (Telemetry Streams)"
  },

  // Phase 3 Forward Chain: 13 -> 14 -> 15 -> 16 -> 17 -> 18
  {
    id: "edge-13-14",
    fromNode: "node-stage-13",
    fromSide: "right",
    toNode: "node-stage-14",
    toSide: "left",
    label: "13. yieldsInsight (5-Whys Synthesis)"
  },
  {
    id: "edge-14-15",
    fromNode: "node-stage-14",
    fromSide: "right",
    toNode: "node-stage-15",
    toSide: "left",
    label: "14. crystallizesLesson (Codification)"
  },
  {
    id: "edge-15-16",
    fromNode: "node-stage-15",
    fromSide: "right",
    toNode: "node-stage-16",
    toSide: "left",
    label: "15. triggersGovernanceChange"
  },
  {
    id: "edge-16-17",
    fromNode: "node-stage-16",
    fromSide: "right",
    toNode: "node-stage-17",
    toSide: "left",
    label: "16. enables (Behavioral Mandate)"
  },
  {
    id: "edge-17-18",
    fromNode: "node-stage-17",
    fromSide: "right",
    toNode: "node-stage-18",
    toSide: "left",
    label: "17. crystallizesCapability"
  },

  // ==========================================
  // CLOSED CYBERNETIC RETURN LOOPS (STEP 19 + FAST-PATHS)
  // ==========================================
  // Primary Return Loop: 18 -> 1 (refinesIntent)
  {
    id: "edge-return-18-1",
    fromNode: "node-stage-18",
    fromSide: "bottom",
    toNode: "node-stage-1",
    toSide: "bottom",
    label: "18. refinesIntent / Intent Refinement (PRIMARY CLOSED LOOP ⟲)"
  },
  // Fast-Path Governance Feedback: 16 -> 1 (triggersIntent)
  {
    id: "edge-fast-16-1",
    fromNode: "node-stage-16",
    fromSide: "top",
    toNode: "node-stage-1",
    toSide: "top",
    label: "triggersIntent (Policy Re-Inception)"
  },
  // Fast-Path Architectural Drift Remediation: 16 -> 3 (amends_adr)
  {
    id: "edge-fast-16-3",
    fromNode: "node-stage-16",
    fromSide: "top",
    toNode: "node-stage-3",
    toSide: "bottom",
    label: "Fast-Path Drift Remediation (amends_adr)"
  },
  // Empirical Outcome Hypothesis Validation: 12 -> 3
  {
    id: "edge-val-12-3",
    fromNode: "node-stage-12",
    fromSide: "top",
    toNode: "node-stage-3",
    toSide: "bottom",
    label: "validatesHypothesis (Empirical Confirmation)"
  },
  // Affect Ergonomics Feedback: 12 -> 16
  {
    id: "edge-affect-12-16",
    fromNode: "node-stage-12",
    fromSide: "bottom",
    toNode: "node-stage-16",
    toSide: "bottom",
    label: "PANAS Cognitive Vitality / DevEx Feedback"
  }
];

const canvas = { nodes, edges };

fs.writeFileSync(targetCanvasPath, JSON.stringify(canvas, null, 2), 'utf8');
console.log(`✅ Successfully generated visual canvas with ${nodes.length} nodes and ${edges.length} edges at: ${targetCanvasPath}`);
