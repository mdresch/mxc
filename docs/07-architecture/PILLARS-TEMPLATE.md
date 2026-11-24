---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating / Planning"
pmbok_process: "5.3 Define Scope & Architectural Strategy Formulation"
lifecycle_stage: "Stage 5.5 (Pillars Exercise)"
governance_policy: "approve-charter"
inputs:
  - "Project-Charter.md"
  - "Ideation-Document.md (Hypotheses)"
  - "Benefits-Statement.md"
process: "Decompose Project Charter objectives into mutually exclusive, collectively exhaustive architectural and functional pillars"
outputs:
  - "PILLARS-EXERCISE.md"
  - "Pillar-to-ADR Coverage Matrix"
---

# Pillars Exercise — <Project Name>

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation` (Initiating / Planning)  
> **Lifecycle Stage:** `Stage 5.5 (Pillars Exercise)` | **Inputs:** Project-Charter.md, Ideation-Document.md, Benefits-Statement.md  
> **Process:** Decompose Project Charter into mutually exclusive, collectively exhaustive architectural and functional pillars  
> **Outputs:** PILLARS-EXERCISE.md, Pillar-to-ADR Coverage Matrix

**Source:** [Project-Charter.md](../project-docs/Project-Charter.md)

---

## 1. Executive Purpose & Strategic Mandate
<Synthesize the core strategic mandate from the Project Charter into 1-2 paragraphs. Define the operational boundary for this exercise: identifying the foundational architectural and capability pillars required to realize the project objectives without leaving gaps or unassigned capability domains.>

---

## 2. Core Architectural Pillars

Decompose the project into 4 to 6 mutually exclusive, collectively exhaustive (MECE) pillars. Each pillar must represent a major capability and architectural domain.

### Pillar 1: <Pillar Name> (e.g., Domain Model & Data Foundation)
- **Domain Focus:** <What capability or subsystem this pillar owns>
- **Strategic Alignment:** <Which Charter objective / Hypothesis this pillar supports>
- **Key Architectural Responsibilities:**
  - <Responsibility 1>
  - <Responsibility 2>
- **Target Deliverables:** <Core modules, stores, or schemas>

### Pillar 2: <Pillar Name> (e.g., Engine & Core Processing Subsystem)
- **Domain Focus:** <What capability or subsystem this pillar owns>
- **Strategic Alignment:** <Which Charter objective / Hypothesis this pillar supports>
- **Key Architectural Responsibilities:**
  - <Responsibility 1>
  - <Responsibility 2>
- **Target Deliverables:** <Engines, pipelines, or background workers>

### Pillar 3: <Pillar Name> (e.g., Telemetry, Event Ingestion & Integration)
- **Domain Focus:** <What capability or subsystem this pillar owns>
- **Strategic Alignment:** <Which Charter objective / Hypothesis this pillar supports>
- **Key Architectural Responsibilities:**
  - <Responsibility 1>
  - <Responsibility 2>
- **Target Deliverables:** <APIs, telemetry hooks, integrations>

### Pillar 4: <Pillar Name> (e.g., Governance, Bayesian Policy Gates & Auditing)
- **Domain Focus:** <What capability or subsystem this pillar owns>
- **Strategic Alignment:** <Which Charter objective / Hypothesis this pillar supports>
- **Key Architectural Responsibilities:**
  - <Responsibility 1>
  - <Responsibility 2>
- **Target Deliverables:** <Decision frames, policy stores, audit registers>

### Pillar 5: <Pillar Name> (e.g., User Interface & Visualization)
- **Domain Focus:** <What capability or subsystem this pillar owns>
- **Strategic Alignment:** <Which Charter objective / Hypothesis this pillar supports>
- **Key Architectural Responsibilities:**
  - <Responsibility 1>
  - <Responsibility 2>
- **Target Deliverables:** <Web dashboard, CLI, interactive widgets>

---

## 3. Pillar-to-ADR Full-Coverage Matrix (100% Invariant)

Every pillar defined above **must be governed by at least one high-level Architectural Decision Record (ADR)**. No pillar may be left floating without an ADR, and every initial ADR must anchor to at least one pillar.

| Pillar ID | Pillar Name | Governing High-Level ADR | ADR Title / Scope | Coverage Status |
|---|---|---|---|:---:|
| **PIL-01** | <Pillar 1 Name> | `ADR-001` | <Title of ADR-001> | Proposed / Covered |
| **PIL-02** | <Pillar 2 Name> | `ADR-002` | <Title of ADR-002> | Proposed / Covered |
| **PIL-03** | <Pillar 3 Name> | `ADR-003` | <Title of ADR-003> | Proposed / Covered |
| **PIL-04** | <Pillar 4 Name> | `ADR-004` | <Title of ADR-004> | Proposed / Covered |
| **PIL-05** | <Pillar 5 Name> | `ADR-005` | <Title of ADR-005> | Proposed / Covered |

---

## 4. Downstream Work Package Derivation Chain

Each Pillar and its governing ADR initiates the formal specification and work breakdown chain:

$$\text{Pillar} \longrightarrow \text{High-Level ADR} \longrightarrow \text{BRD} \longrightarrow \text{FDD} \longrightarrow \text{User Stories (Work Packages)}$$

1. **High-Level ADRs:** Establish technical decisions, system boundaries, and trade-offs per pillar.
2. **BRDs (Business Requirements):** Specify business rules, regulatory constraints, and functional requirements.
3. **FDDs (Functional Design):** Specify data contracts, API schemas, and component interfaces.
4. **User Stories (Work Packages):** Define atomic deliverables with BDD acceptance criteria.  
   **Crucial Invariant:** These User Stories become the concrete **Work Packages** that provide duration, story points, and resource commitments to ground the **Scope (5.1)**, **Schedule (6.1)**, **Cost (7.1)**, and **Resource (9.1)** management plans into the integrated **Project Management Plan (4.2)**.

