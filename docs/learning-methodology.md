# Learning methodology for governance decisions

The gates in this template (`approve-*`, `validate-intent-foundation`) run under **full decision authority**: reasoned Bayesian resolution over a decision frame, with permanent human approval. This is the default for every plan, document and architecture decision, and choosing it never grants autonomy.

## When something else applies

- A decision that recurs often with a small set of actions and scored outcomes, both wins and losses, can use **low authority** (a softmax policy trained with REINFORCE). Declare it only after at least two real, converged cases exist.
- A decision that must always reach a human (safety, compliance, financial, destructive) stays on full authority with `requires_human_approval: true`. That flag outranks every statistic.
- Candidate methods that need data you do not have (Thompson sampling or UCB for positive-only history, multi-stage credit assignment that needs a trace identifier, off-policy evaluation that needs logged action probabilities) are "blocked", not "chosen". Do not create episodes to make a method look viable.

## Per-plan note

Every plan is gated by the same `approve-subsidiary-plan` policy, so no plan has its own learned method. Candidates that could apply later if their constraint is lifted: multi-stage credit assignment for Scope, Schedule and Cost (needs an `Episode.trace_id`), safe bandits with action masking for risk responses, and a softmax policy for nonconformance triage in Quality (waivers stay human). Resource, Stakeholder Engagement, Communications and Procurement have no identified candidate.

Record the methodology choice in the ADR or decision note. Until a selection chain exists, it is not recorded as an episode.

## Catalog, matrix and ledger

`docs/methodologies/catalog.json` lists all 32 methodologies with their state; `docs/methodologies/Tailoring-Matrix.md` pairs needs in the store and in lessons learned with candidates (all hypotheses); the project ledger (`docs/registers/Methodology-Best-Practice-Ledger.md`, scaffolded by `init_project.py`) records which practices are candidates and which, on real episodes, are adopted. Examples are synthetic and are not evidence.
