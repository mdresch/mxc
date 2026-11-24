# SIDPA chain adoption

`docs/chain-coverage.md` and `docs/sequence-and-lessons.md` are the copies from `mdresch/sidpa-template` @ `0e88dd0` (11 Nov 2026, 01:59 Europe/Amsterdam).

MXC uses that chain's stage numbers:

- Stage 6 is the requirement band. ADR, BRD, FDD, and epic frontmatter says `Stage 6 (Requirement: …)`.
- Stage 7 is the PMP and the nine subsidiary plans. Their frontmatter says `Stage 7 (Planning: Integrated PMP & Baselines)`.
- Stage 8 is the implementation readiness notice. Only the template is in the tree. No notice has been issued.

`pmbok/lifecycle/stages.py` uses the same numbers. `python3 -c` against `pmbok.lifecycle.validate_project` reports invariants PASS. Stages 5 and 8 have no non-template evidence. Stages 9, 10, and 12–16 have no evidence. Policy shapes are still absent for `implement-story`, `contract-test-suite`, `empirical-observation`, `ingest-telemetry-signal`, and `resolve-kb-conflict`.

This adoption does not approve the Charter, the benefits statement, the PMP, or Stage 8. The PMP and the nine plans remain scaffolds titled "SIDPA Project".
