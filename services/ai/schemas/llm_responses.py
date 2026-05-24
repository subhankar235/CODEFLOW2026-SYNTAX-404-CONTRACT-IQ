"""
services/ai/schemas/llm_responses.py

Pydantic v2 models that mirror the exact JSON schemas defined in the prompt
templates.  Every LLM response is validated against these models before
being stored or passed to downstream code.

NOTE: Enums are defined locally here rather than imported from the API
service so that the AI service can be imported/tested independently.
All enum values are kept in sync with services/api/app/schemas/response.py.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Mirrored enums (values must stay in sync with api/app/schemas/response.py)
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class ContractType(str, Enum):
    EMPLOYMENT = "Employment"
    NDA = "NDA"
    FREELANCE_SOW = "Freelance/SOW"
    SAAS_SUBSCRIPTION = "SaaS Subscription"
    LEASE_RENTAL = "Lease/Rental"
    PARTNERSHIP = "Partnership"
    IP_LICENSE = "IP License"
    LOAN = "Loan"
    MA = "M&A"
    OTHER = "Other"


class ImpactSeverity(str, Enum):
    CATASTROPHIC = "CATASTROPHIC"
    SEVERE = "SEVERE"
    MODERATE = "MODERATE"
    MINOR = "MINOR"
    NEGLIGIBLE = "NEGLIGIBLE"


class Likelihood(str, Enum):
    CERTAIN = "CERTAIN"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    UNLIKELY = "UNLIKELY"
    RARE = "RARE"


class NegotiationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AcceptanceLikelihood(str, Enum):
    VERY_LIKELY = "VERY_LIKELY"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    UNLIKELY = "UNLIKELY"
    VERY_UNLIKELY = "VERY_UNLIKELY"


class AsymmetryCategory(str, Enum):
    LIABILITY = "liability"
    TERMINATION = "termination"
    PAYMENT = "payment"
    DISPUTE_RESOLUTION = "dispute_resolution"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    INDEMNIFICATION = "indemnification"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    OTHER = "other"


class Enforceability(str, Enum):
    HIGHLY_ENFORCEABLE = "HIGHLY_ENFORCEABLE"
    LIKELY_ENFORCEABLE = "LIKELY_ENFORCEABLE"
    UNCERTAIN = "UNCERTAIN"
    UNLIKELY_ENFORCEABLE = "UNLIKELY_ENFORCEABLE"
    NOT_ENFORCEABLE = "NOT_ENFORCEABLE"


class PrecedentType(str, Enum):
    CASE_LAW = "case_law"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    TREATY = "treaty"



# ---------------------------------------------------------------------------
# risk_analysis.txt  →  LLMRiskAnalysis
# ---------------------------------------------------------------------------

class LLMRiskAnalysis(BaseModel):
    risk_level: RiskLevel
    risk_category: str
    risk_summary: str = Field(..., max_length=200)
    risk_explanation: str = Field(..., max_length=1000)
    problematic_language: Optional[str] = None
    recommendations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# type_detection.txt  →  LLMTypeDetection
# ---------------------------------------------------------------------------

class LLMTypeDetection(BaseModel):
    contract_type: ContractType
    contract_subtype: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_parties: list[str] = Field(default_factory=list)
    governing_law: Optional[str] = None
    effective_date: Optional[str] = None       # ISO date string; parsed later
    reasoning: str


# ---------------------------------------------------------------------------
# consequence.txt  →  LLMConsequence
# ---------------------------------------------------------------------------

class LLMImpactDetail(BaseModel):
    estimated_severity: ImpactSeverity
    description: Optional[str] = None


class LLMConsequence(BaseModel):
    immediate_consequences: list[str] = Field(default_factory=list)
    long_term_consequences: list[str] = Field(default_factory=list)
    financial_impact: LLMImpactDetail
    operational_impact: LLMImpactDetail
    worst_case_scenario: Optional[str] = None
    likelihood: Likelihood
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# summary.txt  →  LLMSummary
# ---------------------------------------------------------------------------

class LLMKeyObligations(BaseModel):
    party_a: list[str] = Field(default_factory=list)
    party_b: list[str] = Field(default_factory=list)


class LLMKeyRights(BaseModel):
    party_a: list[str] = Field(default_factory=list)
    party_b: list[str] = Field(default_factory=list)


class LLMImportantDate(BaseModel):
    label: str
    date: Optional[str] = None
    description: str


class LLMSummary(BaseModel):
    plain_summary: str
    key_obligations: LLMKeyObligations
    key_rights: LLMKeyRights
    important_dates: list[LLMImportantDate] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    overall_risk_level: RiskLevel
    word_count: int = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# power_asymmetry.txt  →  LLMPowerAsymmetry
# ---------------------------------------------------------------------------

class LLMAsymmetricClause(BaseModel):
    clause_id: str
    position_index: int = Field(..., ge=0)
    category: AsymmetryCategory
    description: str
    favours: str              # 'party_a' | 'party_b'
    severity: RiskLevel


class LLMPowerAsymmetry(BaseModel):
    overall_balance_score: float = Field(..., ge=-1.0, le=1.0)
    favoured_party: str       # 'party_a' | 'party_b' | 'balanced'
    asymmetric_clauses: list[LLMAsymmetricClause] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    overall_assessment: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# counter_offer.txt  →  LLMCounterOffer
# ---------------------------------------------------------------------------

class LLMAlternative(BaseModel):
    label: str
    proposed_text: str
    changes_made: list[str] = Field(default_factory=list)
    rationale: Optional[str] = None
    acceptance_likelihood: AcceptanceLikelihood


class LLMCounterOffer(BaseModel):
    original_clause_summary: str
    negotiation_priority: NegotiationPriority
    alternatives: list[LLMAlternative] = Field(min_length=1)
    key_protections_added: list[str] = Field(default_factory=list)
    negotiation_tips: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# precedent.txt  →  LLMPrecedent
# ---------------------------------------------------------------------------

class LLMPrecedentItem(BaseModel):
    type: PrecedentType
    title: str
    citation: Optional[str] = None
    jurisdiction: str
    relevance: str
    favours: str              # 'party_a' | 'party_b' | 'neutral'
    confidence: float = Field(..., ge=0.0, le=1.0)


class LLMPrecedent(BaseModel):
    relevant_precedents: list[LLMPrecedentItem] = Field(default_factory=list)
    applicable_statutes: list[str] = Field(default_factory=list)
    enforceability_assessment: Enforceability
    enforceability_notes: Optional[str] = None
    overall_confidence: float = Field(..., ge=0.0, le=1.0)