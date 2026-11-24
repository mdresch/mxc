"""Static registry of all 49 PMBOK processes and their dependency map."""

from __future__ import annotations

from pmbok.models.enums import KnowledgeArea, ProcessGroup
from pmbok.models.pmbok import PMBOKProcess

# ---------------------------------------------------------------------------
# Dependency map: process_id → list of prerequisite process_ids
# ---------------------------------------------------------------------------

PROCESS_DEPENDENCY_MAP: dict[str, list[str]] = {
    # Initiating
    "4.1": [],
    "13.1": [],
    # Planning — depends on Initiating and subsidiary plans
    "4.2": ["4.1", "5.1", "6.1", "7.1", "8.1", "9.1", "10.1", "11.1", "12.1", "13.2"],
    "5.1": ["4.1"],
    "6.1": ["4.1"],
    "7.1": ["4.1"],
    "8.1": ["4.1", "5.2"],
    "9.1": ["4.1"],
    "10.1": ["4.1"],
    "11.1": ["4.1"],
    "12.1": ["4.1"],
    "13.2": ["13.1"],
    # Planning — internal ordering (Scope)
    "5.2": ["5.1"],
    "5.3": ["5.2"],
    "5.4": ["5.3"],
    # Planning — internal ordering (Schedule)
    "6.2": ["6.1"],
    "6.3": ["6.2"],
    "6.4": ["6.3"],
    "6.5": ["6.4"],
    # Planning — internal ordering (Cost)
    "7.2": ["7.1", "6.5"],
    "7.3": ["7.2"],
    # Planning — internal ordering (Resource)
    "9.2": ["9.1", "5.4"],
    # Planning — internal ordering (Risk)
    "11.2": ["11.1"],
    "11.3": ["11.2"],
    "11.4": ["11.3"],
    "11.5": ["11.4"],
    # Executing
    "4.3": [],
    "4.4": ["4.3"],
    "8.2": [],
    "9.3": [],
    "9.4": ["9.3"],
    "9.5": ["9.4"],
    "10.2": [],
    "11.6": ["11.5"],
    "12.2": ["12.1"],
    "13.3": [],
    # Monitoring & Controlling
    "4.5": [],
    "4.6": [],
    "5.5": ["5.4"],
    "5.6": ["5.4"],
    "6.6": ["6.5"],
    "7.4": ["7.3"],
    "8.3": ["8.2"],
    "9.6": ["9.3"],
    "10.3": ["10.2"],
    "11.7": ["11.6"],
    "12.3": ["12.2"],
    "13.4": ["13.3"],
    # Closing
    "4.7": [],
}

# ---------------------------------------------------------------------------
# All 49 PMBOK processes
# ---------------------------------------------------------------------------

_PROCESS_DATA: list[tuple[str, str, KnowledgeArea, ProcessGroup, list[str]]] = [
    # (process_id, name, knowledge_area, process_group, expected_outputs)
    ("4.1", "Develop Project Charter", KnowledgeArea.INTEGRATION, ProcessGroup.INITIATING,
     ["Project Charter"]),
    ("4.2", "Develop Project Management Plan", KnowledgeArea.INTEGRATION, ProcessGroup.PLANNING,
     ["Project Management Plan"]),
    ("4.3", "Direct and Manage Project Work", KnowledgeArea.INTEGRATION, ProcessGroup.EXECUTING,
     ["Deliverables", "Work Performance Data", "Issue Log"]),
    ("4.4", "Manage Project Knowledge", KnowledgeArea.INTEGRATION, ProcessGroup.EXECUTING,
     ["Lessons Learned Register"]),
    ("4.5", "Monitor and Control Project Work", KnowledgeArea.INTEGRATION, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Reports", "Change Requests"]),
    ("4.6", "Perform Integrated Change Control", KnowledgeArea.INTEGRATION, ProcessGroup.MONITORING_CONTROLLING,
     ["Approved Change Requests", "Change Log"]),
    ("4.7", "Close Project or Phase", KnowledgeArea.INTEGRATION, ProcessGroup.CLOSING,
     ["Final Product/Service/Result Transition", "Final Report"]),
    ("5.1", "Plan Scope Management", KnowledgeArea.SCOPE, ProcessGroup.PLANNING,
     ["Scope Management Plan", "Requirements Management Plan"]),
    ("5.2", "Collect Requirements", KnowledgeArea.SCOPE, ProcessGroup.PLANNING,
     ["Requirements Documentation", "Requirements Traceability Matrix"]),
    ("5.3", "Define Scope", KnowledgeArea.SCOPE, ProcessGroup.PLANNING,
     ["Project Scope Statement"]),
    ("5.4", "Create WBS", KnowledgeArea.SCOPE, ProcessGroup.PLANNING,
     ["Work Breakdown Structure", "WBS Dictionary", "Scope Baseline"]),
    ("5.5", "Validate Scope", KnowledgeArea.SCOPE, ProcessGroup.MONITORING_CONTROLLING,
     ["Accepted Deliverables", "Work Performance Information"]),
    ("5.6", "Control Scope", KnowledgeArea.SCOPE, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Change Requests", "Scope Baseline Updates"]),
    ("6.1", "Plan Schedule Management", KnowledgeArea.SCHEDULE, ProcessGroup.PLANNING,
     ["Schedule Management Plan"]),
    ("6.2", "Define Activities", KnowledgeArea.SCHEDULE, ProcessGroup.PLANNING,
     ["Activity List", "Activity Attributes", "Milestone List"]),
    ("6.3", "Sequence Activities", KnowledgeArea.SCHEDULE, ProcessGroup.PLANNING,
     ["Project Schedule Network Diagrams"]),
    ("6.4", "Estimate Activity Durations", KnowledgeArea.SCHEDULE, ProcessGroup.PLANNING,
     ["Duration Estimates", "Basis of Estimates"]),
    ("6.5", "Develop Schedule", KnowledgeArea.SCHEDULE, ProcessGroup.PLANNING,
     ["Project Schedule", "Schedule Baseline", "Schedule Data"]),
    ("6.6", "Control Schedule", KnowledgeArea.SCHEDULE, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Schedule Forecasts", "Change Requests"]),
    ("7.1", "Plan Cost Management", KnowledgeArea.COST, ProcessGroup.PLANNING,
     ["Cost Management Plan"]),
    ("7.2", "Estimate Costs", KnowledgeArea.COST, ProcessGroup.PLANNING,
     ["Cost Estimates", "Basis of Estimates"]),
    ("7.3", "Determine Budget", KnowledgeArea.COST, ProcessGroup.PLANNING,
     ["Cost Baseline", "Project Funding Requirements"]),
    ("7.4", "Control Costs", KnowledgeArea.COST, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Cost Forecasts", "Change Requests"]),
    ("8.1", "Plan Quality Management", KnowledgeArea.QUALITY, ProcessGroup.PLANNING,
     ["Quality Management Plan", "Quality Metrics"]),
    ("8.2", "Manage Quality", KnowledgeArea.QUALITY, ProcessGroup.EXECUTING,
     ["Quality Reports", "Test and Evaluation Documents"]),
    ("8.3", "Control Quality", KnowledgeArea.QUALITY, ProcessGroup.MONITORING_CONTROLLING,
     ["Quality Control Measurements", "Verified Deliverables"]),
    ("9.1", "Plan Resource Management", KnowledgeArea.RESOURCE, ProcessGroup.PLANNING,
     ["Resource Management Plan", "Team Charter"]),
    ("9.2", "Estimate Activity Resources", KnowledgeArea.RESOURCE, ProcessGroup.PLANNING,
     ["Resource Requirements", "Basis of Estimates", "Resource Breakdown Structure"]),
    ("9.3", "Acquire Resources", KnowledgeArea.RESOURCE, ProcessGroup.EXECUTING,
     ["Physical Resource Assignments", "Project Team Assignments"]),
    ("9.4", "Develop Team", KnowledgeArea.RESOURCE, ProcessGroup.EXECUTING,
     ["Team Performance Assessments"]),
    ("9.5", "Manage Team", KnowledgeArea.RESOURCE, ProcessGroup.EXECUTING,
     ["Change Requests", "Project Management Plan Updates"]),
    ("9.6", "Control Resources", KnowledgeArea.RESOURCE, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Change Requests"]),
    ("10.1", "Plan Communications Management", KnowledgeArea.COMMUNICATIONS, ProcessGroup.PLANNING,
     ["Communications Management Plan"]),
    ("10.2", "Manage Communications", KnowledgeArea.COMMUNICATIONS, ProcessGroup.EXECUTING,
     ["Project Communications"]),
    ("10.3", "Monitor Communications", KnowledgeArea.COMMUNICATIONS, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Change Requests"]),
    ("11.1", "Plan Risk Management", KnowledgeArea.RISK, ProcessGroup.PLANNING,
     ["Risk Management Plan"]),
    ("11.2", "Identify Risks", KnowledgeArea.RISK, ProcessGroup.PLANNING,
     ["Risk Register", "Risk Report"]),
    ("11.3", "Perform Qualitative Risk Analysis", KnowledgeArea.RISK, ProcessGroup.PLANNING,
     ["Risk Register Updates"]),
    ("11.4", "Perform Quantitative Risk Analysis", KnowledgeArea.RISK, ProcessGroup.PLANNING,
     ["Risk Report Updates"]),
    ("11.5", "Plan Risk Responses", KnowledgeArea.RISK, ProcessGroup.PLANNING,
     ["Risk Register Updates", "Risk Report Updates", "Change Requests"]),
    ("11.6", "Implement Risk Responses", KnowledgeArea.RISK, ProcessGroup.EXECUTING,
     ["Change Requests"]),
    ("11.7", "Monitor Risks", KnowledgeArea.RISK, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Change Requests"]),
    ("12.1", "Plan Procurement Management", KnowledgeArea.PROCUREMENT, ProcessGroup.PLANNING,
     ["Procurement Management Plan", "Procurement Strategy", "Bid Documents"]),
    ("12.2", "Conduct Procurements", KnowledgeArea.PROCUREMENT, ProcessGroup.EXECUTING,
     ["Selected Sellers", "Agreements"]),
    ("12.3", "Control Procurements", KnowledgeArea.PROCUREMENT, ProcessGroup.MONITORING_CONTROLLING,
     ["Closed Procurements", "Work Performance Information"]),
    ("13.1", "Identify Stakeholders", KnowledgeArea.STAKEHOLDER, ProcessGroup.INITIATING,
     ["Stakeholder Register"]),
    ("13.2", "Plan Stakeholder Engagement", KnowledgeArea.STAKEHOLDER, ProcessGroup.PLANNING,
     ["Stakeholder Engagement Plan"]),
    ("13.3", "Manage Stakeholder Engagement", KnowledgeArea.STAKEHOLDER, ProcessGroup.EXECUTING,
     ["Change Requests", "Stakeholder Engagement Plan Updates"]),
    ("13.4", "Monitor Stakeholder Engagement", KnowledgeArea.STAKEHOLDER, ProcessGroup.MONITORING_CONTROLLING,
     ["Work Performance Information", "Change Requests"]),
]

PMBOK_PROCESSES: list[PMBOKProcess] = [
    PMBOKProcess(
        process_id=pid,
        name=name,
        knowledge_area=area,
        process_group=group,
        prerequisites=PROCESS_DEPENDENCY_MAP.get(pid, []),
        expected_outputs=outputs,
    )
    for pid, name, area, group, outputs in _PROCESS_DATA
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_processes_by_group(group: ProcessGroup) -> list[PMBOKProcess]:
    """Return all PMBOK processes belonging to the given process group."""
    return [p for p in PMBOK_PROCESSES if p.process_group == group]


def get_processes_by_area(area: KnowledgeArea) -> list[PMBOKProcess]:
    """Return all PMBOK processes belonging to the given knowledge area."""
    return [p for p in PMBOK_PROCESSES if p.knowledge_area == area]


class ProcessRegistry:
    """Registry for accessing PMBOK processes and their metadata."""

    def __init__(self):
        """Initialize the registry with built-in PMBOK processes."""
        self.processes = PMBOK_PROCESSES
        self._by_id = {p.process_id: p for p in PMBOK_PROCESSES}

    def get_process(self, process_id: str) -> PMBOKProcess | None:
        """Get a process by its ID (e.g., '4.1')."""
        return self._by_id.get(process_id)

    def get_processes_by_group(self, group: ProcessGroup) -> list[PMBOKProcess]:
        """Get all processes in a specific process group."""
        return [p for p in self.processes if p.process_group == group]

    def get_processes_by_area(self, area: KnowledgeArea) -> list[PMBOKProcess]:
        """Get all processes in a specific knowledge area."""
        return [p for p in self.processes if p.knowledge_area == area]

    def get_process_dependencies(self, process_id: str) -> list[str]:
        """Get prerequisite process IDs for a given process."""
        return PROCESS_DEPENDENCY_MAP.get(process_id, [])

    def get_all_processes(self) -> list[PMBOKProcess]:
        """Get all registered PMBOK processes."""
        return self.processes

    def is_valid_process_id(self, process_id: str) -> bool:
        """Check if a process ID is valid."""
        return process_id in self._by_id

