"""
Summary card and pros/cons schemas — PRD Features 4 & 7.

GET /api/v1/summary/{contractId} returns SummaryResponse.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.response import SignVerdict, NegotiatingPower


# ---------------------------------------------------------------------------
# Feature 4: Plain-Language Summary Card
# ---------------------------------------------------------------------------


class SummaryCard(BaseModel):
    """Hero summary card generated after all clauses are analysed (PRD Feature 4)."""

    contract_id: UUID

    one_liner: str = Field(
        ..., description="Single sentence: contract + key implication"
    )
    should_you_sign: SignVerdict
    top_3_concerns: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 most important things to address before signing",
    )
    top_2_positives: list[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 favourable aspects",
    )
    overall_risk_score: int = Field(..., ge=0, le=100)
    negotiating_power: NegotiatingPower

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Feature 7: Pros vs Cons Snapshot
# ---------------------------------------------------------------------------


class ProsConsItem(BaseModel):
    """Single item in the pros/cons snapshot."""

    dimension: str = Field(
        ...,
        description="financial | liability | ip | exit_rights | obligations",
    )
    point: str


class ProsConsResult(BaseModel):
    """Two-column pros/cons snapshot (PRD Feature 7)."""

    contract_id: UUID

    pros: list[ProsConsItem] = Field(default_factory=list)
    cons: list[ProsConsItem] = Field(default_factory=list)
    verdict: str = Field(..., description="One-sentence overall assessment")

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Combined response for GET /summary/{contractId}
# ---------------------------------------------------------------------------


class SummaryResponse(BaseModel):
    """Combined summary + pros/cons for a completed scan."""

    summary: SummaryCard
    pros_cons: Optional[ProsConsResult] = None
