"""
Shared response schemas and enums used across the API.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    """Risk severity levels for clauses (PRD Feature 1)."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class ContractType(str, Enum):
    """Contract types as defined in PRD Feature 2 (10 exact types)."""
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
    """Severity of impact from clause consequences."""
    CATASTROPHIC = "CATASTROPHIC"
    SEVERE = "SEVERE"
    MODERATE = "MODERATE"
    MINOR = "MINOR"
    NEGLIGIBLE = "NEGLIGIBLE"


class Likelihood(str, Enum):
    """Likelihood of consequence occurrence."""
    CERTAIN = "CERTAIN"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    UNLIKELY = "UNLIKELY"
    RARE = "RARE"


class NegotiationPriority(str, Enum):
    """Priority level for counter-offer negotiation."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AcceptanceLikelihood(str, Enum):
    """Likelihood of counter-offer acceptance."""
    VERY_LIKELY = "VERY_LIKELY"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    UNLIKELY = "UNLIKELY"
    VERY_UNLIKELY = "VERY_UNLIKELY"


class AsymmetryCategory(str, Enum):
    """Categories of power asymmetry in contracts."""
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
    """Enforceability assessment for precedents."""
    HIGHLY_ENFORCEABLE = "HIGHLY_ENFORCEABLE"
    LIKELY_ENFORCEABLE = "LIKELY_ENFORCEABLE"
    UNCERTAIN = "UNCERTAIN"
    UNLIKELY_ENFORCEABLE = "UNLIKELY_ENFORCEABLE"
    NOT_ENFORCEABLE = "NOT_ENFORCEABLE"


class PrecedentType(str, Enum):
    """Types of legal precedents."""
    CASE_LAW = "case_law"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    TREATY = "treaty"


class ClauseType(str, Enum):
    """Types of contract clauses."""
    PAYMENT = "payment"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    NON_COMPETE = "non_compete"
    NON_SOLICITATION = "non_solicitation"
    FORCE_MAJEURE = "force_majeure"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    ASSIGNMENT = "assignment"
    AMENDMENT = "amendment"
    WARRANTY = "warranty"
    REPRESENTATION = "representation"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Shared Response Models
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# New enums required by PRD Features 4, 9, 11
# ---------------------------------------------------------------------------

class SignVerdict(str, Enum):
    """Signing recommendation from the summary card (PRD Feature 4)."""
    YES_AS_IS = "Yes as-is"
    YES_WITH_CHANGES = "Yes with changes"
    NO = "No"


class NegotiatingPower(str, Enum):
    """User's overall negotiating position (PRD Feature 4)."""
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"


class EnforcementLikelihood(str, Enum):
    """Likelihood a clause will be enforced as written (PRD Feature 9)."""
    VERY_LIKELY = "Very Likely"
    LIKELY = "Likely"
    UNCERTAIN = "Uncertain"
    UNLIKELY = "Unlikely"


# ---------------------------------------------------------------------------
# Shared Response Models
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Standard error detail — matches reviewer error shape requirement."""
    error: str
    detail: str
    code: str


class APIError(BaseModel):
    """Standard API error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int