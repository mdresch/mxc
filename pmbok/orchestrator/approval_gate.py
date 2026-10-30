"""ApprovalGate — blocks workflow advancement pending user decisions."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Callable, Awaitable

from pmbok.models.approval import ApprovalDecision
from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus
from pmbok.models.pmbok import ProcessMap

if TYPE_CHECKING:
    from pmbok.models.business_case import BusinessCase
    from pmbok.models.ideation import IdeationSummary
    from pmbok.storage.state_store import StateStore

# ── Gate name constants ───────────────────────────────────────────────────────

GATE_1_IDEATION = "GATE_1_IDEATION"
GATE_2_BUSINESS_CASE = "GATE_2_BUSINESS_CASE"
GATE_3_INITIATING = "GATE_3_INITIATING"
GATE_4_PLANNING = "GATE_4_PLANNING"
GATE_5_EXECUTING = "GATE_5_EXECUTING"
GATE_6_MONITORING_CONTROLLING = "GATE_6_MONITORING_CONTROLLING"

GATE_NAMES: dict[ProcessGroup, str] = {
    ProcessGroup.INITIATING: GATE_3_INITIATING,
    ProcessGroup.PLANNING: GATE_4_PLANNING,
    ProcessGroup.EXECUTING: GATE_5_EXECUTING,
    ProcessGroup.MONITORING_CONTROLLING: GATE_6_MONITORING_CONTROLLING,
}

# Type alias for the optional user-interface callback
UICallback = Callable[[str], Awaitable[ApprovalDecision]]


class ApprovalGate:
    """
    Blocks workflow advancement until the user explicitly approves.
    On rejection, returns an ApprovalDecision with revision instructions.
    """

    def __init__(
        self,
        state_store: "StateStore",
        run_id: str,
        user_interface: UICallback | None = None,
    ) -> None:
        self._state_store = state_store
        self._run_id = run_id
        self._user_interface = user_interface

    # ── Public API ────────────────────────────────────────────────────────────

    async def present(
        self,
        artifact: "IdeationSummary | BusinessCase | ProcessGroup",
        rendered_markdown: str,
        gate_name: str | None = None,
        decision_override: ApprovalDecision | None = None,
    ) -> ApprovalDecision:
        """
        Emit the rendered artifact to the user interface and block until a
        decision is received.

        Parameters
        ----------
        artifact:
            The artifact being reviewed (used to derive gate_name when not
            provided explicitly).
        rendered_markdown:
            Human-readable representation emitted to the UI / stdout.
        gate_name:
            Optional explicit gate name for persistence.  When omitted the
            gate name is derived from *artifact*.
        decision_override:
            When provided, skip waiting and use this decision directly
            (useful for CLI / testing).
        """
        resolved_gate_name = gate_name or self._derive_gate_name(artifact)

        if decision_override is not None:
            decision = decision_override
        elif self._user_interface is not None:
            decision = await self._user_interface(rendered_markdown)
        else:
            decision = await self._cli_prompt(rendered_markdown)

        # Persist the decision
        await self._state_store.save_gate(
            run_id=self._run_id,
            gate_name=resolved_gate_name,
            status=decision.status,
            decided_at=decision.decided_at,
            revision_instructions=decision.revision_instructions,
        )

        return decision

    def is_group_complete(
        self, process_map: ProcessMap, group: ProcessGroup
    ) -> bool:
        """
        Return True only when ALL processes in *group* have status == COMPLETE.
        A single BLOCKED (or any non-COMPLETE) process returns False.
        """
        for state in process_map.processes:
            # Identify which group this process belongs to by looking up the
            # process registry — we only care about processes in *group*.
            from pmbok.process_registry import get_processes_by_group

            group_process_ids = {
                p.process_id for p in get_processes_by_group(group)
            }
            if state.process_id in group_process_ids:
                if state.status != ProcessStatus.COMPLETE:
                    return False
        return True

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _derive_gate_name(
        artifact: "IdeationSummary | BusinessCase | ProcessGroup",
    ) -> str:
        """Derive a gate name string from the artifact type."""
        # Avoid circular imports by checking type names at runtime
        type_name = type(artifact).__name__
        if type_name == "IdeationSummary":
            return GATE_1_IDEATION
        if type_name == "BusinessCase":
            return GATE_2_BUSINESS_CASE
        if isinstance(artifact, ProcessGroup):
            return GATE_NAMES.get(artifact, f"GATE_{artifact.value.upper()}")
        return f"GATE_{type_name.upper()}"

    @staticmethod
    async def _cli_prompt(rendered_markdown: str) -> ApprovalDecision:
        """
        Fallback CLI prompt: print the artifact and ask for approve/reject.
        Runs the blocking input() call in a thread to stay async-safe.
        """
        print(rendered_markdown, flush=True)
        print("\n--- Approval Gate ---", flush=True)

        loop = asyncio.get_event_loop()

        def _read_decision() -> ApprovalDecision:
            while True:
                choice = input("Approve or reject? [approve/reject]: ").strip().lower()
                if choice in ("approve", "a"):
                    return ApprovalDecision(status=ApprovalStatus.APPROVED)
                if choice in ("reject", "r"):
                    instructions = input(
                        "Enter revision instructions (required): "
                    ).strip()
                    if not instructions:
                        print("Revision instructions cannot be empty.", file=sys.stderr)
                        continue
                    return ApprovalDecision(
                        status=ApprovalStatus.REJECTED,
                        revision_instructions=instructions,
                    )
                print("Please enter 'approve' or 'reject'.", file=sys.stderr)

        return await loop.run_in_executor(None, _read_decision)
