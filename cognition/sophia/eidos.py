import time
from typing import List, Union, Any, Optional
from pydantic import BaseModel, Field

# [SRC:axis_1] Shared Schemas for Sophia/Clotho Reasoning Logic

class TechnicalClaim(BaseModel):
    """Represents a technical claim made by the agent."""
    claim: str = Field(description="The technical claim (e.g., 'VRAM usage', 'NGL layers')")
    value: Any = Field(description="The value asserted for this claim")
    evidence: Optional[str] = Field(None, description="The rationale or evidence source for this claim")
    verified: bool = False

class SophiaOutput(BaseModel):
    """Structured output for Sophia's reasoning and actions."""
    thought: str = Field(description="Internal reasoning process (Chain of Thought)")
    technical_claims: List[TechnicalClaim] = Field(default_factory=list)
    tool_calls: List[dict] = Field(default_factory=list, description="List of tools to execute")
    final_response: Optional[str] = Field(None, description="The human-readable answer if no tools are needed")

class InconsistencyEvidence(BaseModel):
    """Records a mismatch between reasoning and reality."""
    axis: int = 11
    claim: str
    reasoning_value: Any
    reality_value: Any
    timestamp: float = Field(default_factory=time.time)

class ReasoningState(BaseModel):
    task: str
    session_id: str = "default"
    draft: Optional[str] = None
    critique: Optional[str] = None
    final_output: Optional[str] = None
    iteration: int = 0
    tool_calls: Optional[List[dict]] = None
    error_message: Optional[str] = None
    flags: dict = Field(default_factory=dict)

class CritiqueResult(BaseModel):
    is_valid: bool
    flaws: List[str]
    suggestions: List[str]
    confidence_score: float = 1.0
