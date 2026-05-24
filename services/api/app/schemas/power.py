"""
Power asymmetry schemas — PRD Feature 5.

GET /api/v1/power/{contractId} returns PowerAnalysisResult.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class KeyImbalance(BaseModel):
    """A single clause that skews power heavily toward one party."""
    clause: str = Field(..., description="Short excerpt or identifier of the clause")
    why: str = Field(..., description="Explanation of why this clause is imbalanced")
    score: int = Field(..., ge=-100, le=100, description="Per-clause power score")


# ---------------------------------------------------------------------------
# Main response model — matches AGENT_CONTEXT.md SSE event_type='power_result'
# ---------------------------------------------------------------------------

class PowerAnalysisResult(BaseModel):
    """Power asymmetry analysis for a completed scan (PRD Feature 5)."""
    contract_id: UUID

    # Core score: -100 (heavily favours counterparty) → +100 (heavily favours user)
    power_score: int = Field(..., ge=-100, le=100)
    power_label: str = Field(
        ...,
        description=(
            "Human-readable label, e.g. 'Strongly Favors Counterparty', "
            "'Slightly Favors You', 'Balanced'"
        ),
    )

    # Detail arrays — must be arrays, never null (PRD API contract)
    key_imbalances: list[KeyImbalance] = Field(default_factory=list)
    leverage_points: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
