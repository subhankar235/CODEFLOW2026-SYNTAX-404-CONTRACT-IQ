"""
Counter-offer schemas — PRD Feature 6.

POST /api/v1/counter-offer/{clauseId}  → 202 Accepted
GET  /api/v1/counter-offer/{clauseId}  → CounterOfferResult
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class CounterOfferVersion(BaseModel):
    """One rewritten variant of a risky clause (PRD Feature 6)."""
    clause_text: str
    explanation: str = Field(..., description="Why this rewrite is better for the user")


# ---------------------------------------------------------------------------
# Main response model
# ---------------------------------------------------------------------------

class CounterOfferResult(BaseModel):
    """Three negotiation variants for a HIGH-risk clause (PRD Feature 6)."""
    clause_id: UUID

    aggressive: CounterOfferVersion
    balanced: CounterOfferVersion
    conservative: CounterOfferVersion

    # Ready-to-send 2-sentence email — never null per PRD
    negotiation_email: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Status response for polling (after POST 202)
# ---------------------------------------------------------------------------

class CounterOfferStatus(BaseModel):
    """Polling response for counter-offer generation task."""
    clause_id: UUID
    status: str = Field(..., description="queued | processing | complete | failed")
    result: Optional[CounterOfferResult] = None
    error_message: Optional[str] = None
