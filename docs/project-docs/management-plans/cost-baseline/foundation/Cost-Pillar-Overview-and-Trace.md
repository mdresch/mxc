---
artifact_id: cost-foundation-pillar-overview-trace
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.D-0P
depends_on:
  - 6.A-7
  - 6.B-7
---

# Cost Pillar Overview and Trace — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Traces project outcomes and the 6 Topic Pillars (TP-01 through TP-06) to cost drivers, work packages, and financial boundaries.

## 1. Topic pillar cost driver trace

| Topic Pillar | Strategic outcome | Scope / WBS reference | Schedule wave | Primary cost driver | Expected cost range (USD) | Financial boundary source |
|---|---|---|:---:|---|:---:|---|
| **—** | Governance & Baseline Integrity | WBS 1.0 | Wave 1 | PM / Architect reconciliation hours | \$1,100 – \$1,300 | Project Charter authority limit |
| **TP-01 Isolation** | Hyper-V Gen 2 VM boundary & guest fidelity | WBS 2.1, 2.2 | Wave 1 | Platform contractor review & in-guest testing | \$1,800 – \$2,200 | Labor estimates ($12\text{h}$) |
| **TP-02 Ingress** | Zero-cold-start illusion via HTTP socket hold | WBS 3.1, 3.2, 3.3 | Wave 3 | Gateway contractor proxy architecture & tests | \$1,410 – \$1,750 | Labor estimates ($10\text{h}$) |
| **TP-03 Image supply** | Immutable clean production VHDX & warm checkpoint | WBS 4.1, 4.2 | Waves 1–2 | Release contractor bake pipeline & snapshot audit | \$1,500 – \$1,850 | Labor estimates ($10\text{h}$) |
| **TP-04 Paused footprint** | Zero idle CPU/GPU, trimmed RAM, sub-300ms resume | WBS 5.1, 5.2, 5.3 | Wave 2 | Platform contractor PerfMon & stopwatch audits | \$1,500 – \$1,850 | Labor estimates ($10\text{h}$) |
| **TP-05 Session sterility** | Disposable VM lifecycle with differencing disk detachment | WBS 6.1, 6.2, 6.3, 6.4 | Waves 1–2 | Security contractor Port ACL & disk diff audits | \$1,620 – \$2,000 | Labor estimates ($10\text{h}$) |
| **TP-06 Pool & wake hygiene** | Sub-second replenish, surge scale, PRNG reset, reaper | WBS 7.1, 7.2, 7.3, 7.4 | Waves 3–4 | SRE contractor daemon loops & load tests | \$1,870 – \$2,290 | Labor estimates ($12\text{h}$) |
| **—** | Integrated Phase 1 Acceptance Gate | WBS 8.0 | Wave 5 | Multi-agent test harness & PR gate sign-off | \$2,600 – \$3,150 | Labor estimates ($18\text{h}$) |
| **—** | AI Agent Reasoning Computation | All WBS | Waves 1–5 | LLM API token consumption ($10.6\text{M}$ tokens) | \$300 – \$450 | AI turn forecasts ($208.8\text{ turns}$) |
| **Total Base Cost** | **Phase 1 Delivery** | **WBS 1.0–8.0** | **Waves 1–5** | **90h Contractor Labor + AI Compute** | **\$13,460 – \$16,790** | **Within \$25,000 threshold** |

---

## 2. Strategic ROI and financial findings

1. **Massive Labor Efficiency via Agentic Workers**:
   - Without autonomous agent workers, delivering 17 user stories across 6 technical pillars would require an estimated 480 hours of manual coding ($\approx \$76,800$ at blended \$160/hr).
   - Autonomous agents reduce required human labor to **90 review/governance hours** ($\approx \$14,290$) plus **\$375 in AI compute**, achieving an estimated net financial savings of **$\approx \$62,000$ (over $80\%$ reduction)**.
2. **Authority Headroom**:
   - Even including a 15% cost contingency reserve and a \$3,500 management reserve, the total Phase 1 budget is **\$20,365**, fully compliant with the Project Manager's delegated threshold of **\$25,000**.
