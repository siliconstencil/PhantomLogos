import time
from typing import Any

from pydantic import BaseModel, Field

# [SRC:axis_1] Shared Schemas for Sophia/Clotho Reasoning Logic


class TechnicalClaim(BaseModel):
    """Represents a technical claim made by the agent."""

    claim: str = Field(description="The technical claim (e.g., 'VRAM usage', 'NGL layers')")
    value: Any = Field(description="The value asserted for this claim")
    evidence: str | None = Field(
        None, description="The rationale or evidence source for this claim"
    )
    verified: bool = False


class SophiaOutput(BaseModel):
    """Structured output for Sophia's reasoning and actions."""

    thought: str = Field(description="Internal reasoning process (Chain of Thought)")
    technical_claims: list[TechnicalClaim] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list, description="List of tools to execute")
    final_response: str | None = Field(
        None, description="The human-readable answer if no tools are needed"
    )


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
    draft: str | None = None
    critique: str | None = None
    final_output: str | None = None
    iteration: int = 0
    tool_calls: list[dict] | None = None
    error_message: str | None = None
    flags: dict = Field(default_factory=dict)


class CritiqueResult(BaseModel):
    is_valid: bool
    flaws: list[str]
    suggestions: list[str]
    confidence_score: float = 1.0


class ConstraintViolation(BaseModel):
    constraint: str = Field(description="The system constraint that was violated")
    severity: str = Field(description="Severity level: critical, warning, info")
    detail: str = Field(description="Explanation of the violation")


class ConstraintValidationResult(BaseModel):
    is_valid: bool = Field(description="True if no constraints are violated")
    violations: list[ConstraintViolation] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
