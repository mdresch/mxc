"""
ADPA V7 BABOK Models.

This module defines the business-specific schemas for BABOK entities,
intended to be used within the generic 'payload' field of the 
EntityVersionEnvelope.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DesignOptionStatus(str, Enum):
    PROPOSED = "proposed"
    UNDER_ANALYSIS = "under_analysis"
    RETIRED = "retired"
    REJECTED = "rejected"
    RECOMMENDED = "recommended"
    APPROVED = "approved"


class DesignOptionType(str, Enum):
    ARCHITECTURAL = "architectural"
    PROCESSED = "processed"
    TECHNOLOGICAL = "technological"
    ORGANIZATIONAL = "organizational"
    OTHER = "other"


class DesignOptionPayload(BaseModel):
    """
    A governed, traceable proposal for solving a defined business problem
    under stated assumptions, constraints, and trade-offs.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    design_option_id: str = Field(description="Canonical identity key")
    name: str = Field(description="Human-readable name of the option")
    summary: str = Field(description="Concise description of the solution approach")
    problem_context: str = Field(description="The specific gap or need this option addresses")
    
    # Reference links (IDs of other registered entities)
    business_need_ref: List[str] = Field(default_factory=list, description="IDs of linked BusinessNeed entities")
    capability_gap_ref: List[str] = Field(default_factory=list, description="IDs of linked CapabilityGap entities")
    requirements_ref: List[str] = Field(default_factory=list, description="IDs of linked Requirement entities")
    objectives_ref: List[str] = Field(default_factory=list, description="IDs of linked BusinessObjective entities")
    
    option_type: DesignOptionType = DesignOptionType.ARCHITECTURAL
    status: DesignOptionStatus = DesignOptionStatus.PROPOSED
    
    rationale: str = Field(description="Why this option is being considered")
    assumptions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    benefits_expected: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    
    decision_state: str = "under_analysis"
    source_artifact: Optional[str] = None
