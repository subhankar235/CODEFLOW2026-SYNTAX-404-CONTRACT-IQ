"""
Clause-related schemas for API responses.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.response import (
    RiskLevel,
    ImpactSeverity,
    Likelihood,
    AcceptanceLikelihood,
    NegotiationPriority,
    AsymmetryCategory,
    Enforceability,
    PrecedentType,
)


# ---------------------------------------------------------------------------
# Feature 1: Clause Risk Analysis
# ---------------------------------------------------------------------------


class ClauseRecommendation(BaseModel):
    """Recommendation for clause risk mitigation."""

    text: str


class ClauseResult(BaseModel):
    """Complete result of clause risk analysis (Feature 1)."""

    clause_id: UUID
    position_index: int = Field(..., ge=0)
    text: str

    # Risk analysis fields
    risk_level: RiskLevel
    risk_category: str
    risk_summary: str = Field(..., max_length=200)
    risk_explanation: str = Field(..., max_length=1000)
    problematic_language: Optional[str] = None
    recommendations: list[ClauseRecommendation] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    # Metadata
    model_used: Optional[str] = None
    processing_time_ms: Optional[int] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Additional Clause Analysis Results
# ---------------------------------------------------------------------------


class ClauseTypeDetection(BaseModel):
    """Result of clause type detection."""

    clause_id: UUID
    position_index: int
    detected_types: list[str] = Field(default_factory=list)
    primary_type: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ClauseConsequence(BaseModel):
    """Result of consequence analysis."""

    clause_id: UUID
    position_index: int
    immediate_consequences: list[str] = Field(default_factory=list)
    long_term_consequences: list[str] = Field(default_factory=list)
    financial_impact_severity: ImpactSeverity
    operational_impact_severity: ImpactSeverity
    worst_case_scenario: Optional[str] = None
    likelihood: Likelihood
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ClauseSummary(BaseModel):
    """Result of clause summarization."""

    clause_id: UUID
    position_index: int
    plain_summary: str
    key_obligations: list[str] = Field(default_factory=list)
    key_rights: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    word_count: int = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ClausePowerAsymmetry(BaseModel):
    """Result of power asymmetry analysis."""

    clause_id: UUID
    position_index: int
    has_asymmetry: bool
    asymmetry_type: Optional[AsymmetryCategory] = None
    summary: Optional[str] = None
    favoured_party: Optional[str] = None  # 'party_a' | 'party_b'
    risks: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ClauseCounterOffer(BaseModel):
    """Result of counter-offer suggestions."""

    clause_id: UUID
    position_index: int
    original_summary: str
    negotiation_priority: NegotiationPriority
    alternatives: list[dict] = Field(default_factory=list)  # LLMAlternative
    key_protections: list[str] = Field(default_factory=list)
    negotiation_tips: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ClausePrecedent(BaseModel):
    """Result of precedent search."""

    clause_id: UUID
    position_index: int
    relevant_precedents: list[dict] = Field(default_factory=list)  # LLMPrecedentItem
    applicable_statutes: list[str] = Field(default_factory=list)
    enforceability: Enforceability
    enforceability_notes: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Combined Results
# ---------------------------------------------------------------------------


class FullClauseAnalysis(BaseModel):
    """Complete analysis for a single clause."""

    clause_id: UUID
    position_index: int
    text: str

    # All analysis results
    risk_analysis: Optional[ClauseResult] = None
    type_detection: Optional[ClauseTypeDetection] = None
    consequence: Optional[ClauseConsequence] = None
    summary: Optional[ClauseSummary] = None
    power_asymmetry: Optional[ClausePowerAsymmetry] = None
    counter_offer: Optional[ClauseCounterOffer] = None
    precedent: Optional[ClausePrecedent] = None

    # Overall status
    analysis_complete: bool = False
    errors: list[str] = Field(default_factory=list)
