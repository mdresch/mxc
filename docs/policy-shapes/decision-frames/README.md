# Decision frames

A decision frame is the evidence record for one gate decision. It lists the criteria, the options (approve, reject, request revision) and, for each option, a support and confidence score with a source for every score. The gate turns the scores into a ranked recommendation. It does not check the document itself, and a human still accepts or rejects.

- `approve-adr.frame.template.json` is the starting point for an ADR. Copy it to `adr-<NNN>-approval.json` and fill it in.
- **Write the criteria descriptions for the ADR in front of you.** A copied description from another ADR makes the evidence incoherent.
- **The scores are a judgment.** If the author also scores the frame, say so in the source text and score the known weaknesses down.
- **Run:** `agent-learn task-policy-decide --agent-id <project>-governance --task-id approve-adr --decision-frame <frame> --greedy`. Save the output as `docs/policy-shapes/results/adr-<NNN>-decision-result.json`.
- **Record the human decision:** `agent-learn task-policy-adjudicate ... --disposition accept|reject`, then register the episode with `task-episode-register`.
- A frame that was scored against an older text of the document is stale. Re-run the gate after any change to the document.
- Do not store frames or results from a real project in the template. Project frames belong to the project created from it.
