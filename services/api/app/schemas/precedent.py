"""
Legal precedent schemas — PRD Feature 9.

GET /api/v1/precedent/{clauseId} returns PrecedentMatch.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.response import EnforcementLikelihood


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class CaseReference(BaseModel):
    """A single cited court case."""

    name: str
    year: int = Field(..., ge=1800, le=2100)
    jurisdiction: str
    outcome: str


# ---------------------------------------------------------------------------
# Main response model
# ---------------------------------------------------------------------------


class PrecedentMatch(BaseModel):
    """Legal precedent result for a HIGH-risk clause (PRD Feature 9)."""

    clause_id: UUID

    precedent_summary: str = Field(
        ...,
        description="Synthesised paragraph: what courts have typically decided for similar clauses",
    )
    enforcement_likelihood: EnforcementLikelihood
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="0-100 score: RAG retrieval similarity × LLM self-rated confidence",
    )

    # Must be an array, never null
    cited_cases: list[CaseReference] = Field(default_factory=list)

    class Config:
        from_attributes = True
