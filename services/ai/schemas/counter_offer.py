"""
Pydantic models for the counter-offer pipeline.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CounterOfferVersion(BaseModel):
    """A single stance variant of a counter-offer."""

    clause: str = Field(..., min_length=10, description="Full rewritten clause text")
    explanation: str = Field(..., min_length=5, description="Brief explanation of this stance")


class CounterOfferResult(BaseModel):
    """Parsed result from the LLM counter-offer generation."""

    aggressive: CounterOfferVersion
    balanced: CounterOfferVersion
    conservative: CounterOfferVersion
    negotiation_email: str = Field(
        ...,
        description="Professional 2-sentence negotiation email opener",
    )

    @field_validator("negotiation_email")
    @classmethod
    def validate_email_length(cls, v: str) -> str:
        # Soft check: expect roughly 2 sentences (1-3 acceptable)
        sentences = [s.strip() for s in v.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        if len(sentences) < 1:
            raise ValueError("negotiation_email must contain at least one sentence")
        return v

    @field_validator("balanced")
    @classmethod
    def validate_versions_differ(cls, balanced: CounterOfferVersion, info) -> CounterOfferVersion:
        """Ensure balanced clause differs from aggressive (basic check)."""
        if "aggressive" in info.data:
            aggressive = info.data["aggressive"]
            if balanced.clause.strip() == aggressive.clause.strip():
                raise ValueError("balanced and aggressive clauses must differ")
        return balanced


class CounterOfferRequest(BaseModel):
    """Input to the counter-offer pipeline."""

    clause_id: uuid.UUID
    clause_text: str
    risk_category: str
    contract_type: str = "Service Agreement"
    user_role: str = "Client"


class CounterOfferRecord(BaseModel):
    """Full record returned after storing the counter-offer."""

    id: uuid.UUID
    clause_id: uuid.UUID
    result: CounterOfferResult
    favorable_reference_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True