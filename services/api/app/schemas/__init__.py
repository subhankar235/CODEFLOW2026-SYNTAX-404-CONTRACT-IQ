"""services/api/app/schemas package."""

from .response import (
    RiskLevel,
    ContractType,
    ImpactSeverity,
    Likelihood,
    NegotiationPriority,
    AcceptanceLikelihood,
    AsymmetryCategory,
    Enforceability,
    PrecedentType,
    ClauseType,
    SignVerdict,
    NegotiatingPower,
    EnforcementLikelihood,
    ErrorDetail,
    APIError,
    HealthResponse,
    PaginationParams,
    PaginatedResponse,
)

from .clause import (
    ClauseRecommendation,
    ClauseResult,
    ClauseTypeDetection,
    ClauseConsequence,
    ClauseSummary,
    ClausePowerAsymmetry,
    ClauseCounterOffer,
    ClausePrecedent,
    FullClauseAnalysis,
)

from .contract import (
    ContractCreate,
    ContractUpdate,
    ContractRead,
    ContractListItem,
    ContractListResponse,
    ContractAnalysisSummary,
)

from .scan_job import (
    ScanStatus,
    ScanFeatures,
    ScanRequest,
    ScanProgress,
    ScanJobStatus,
    ScanResponse,
    ScanResultSummary,
    ScanResult,
)

from .power import KeyImbalance, PowerAnalysisResult
from .precedent import CaseReference, PrecedentMatch
from .counter_offer import CounterOfferVersion, CounterOfferResult, CounterOfferStatus
from .summary import SummaryCard, ProsConsItem, ProsConsResult, SummaryResponse
from .chat import ConversationTurn, ChatRequest, ChatResponse
from .report import ReportCreate, ReportRead
from .translation import TranslationRequest, TranslationResponse, SUPPORTED_LANGUAGES

__all__ = [
    # ── Enums ──────────────────────────────────────────────────────────────
    "RiskLevel",
    "ContractType",
    "ImpactSeverity",
    "Likelihood",
    "NegotiationPriority",
    "AcceptanceLikelihood",
    "AsymmetryCategory",
    "Enforceability",
    "PrecedentType",
    "ClauseType",
    "ScanStatus",
    "SignVerdict",
    "NegotiatingPower",
    "EnforcementLikelihood",
    # ── Shared response ────────────────────────────────────────────────────
    "ErrorDetail",
    "APIError",
    "HealthResponse",
    "PaginationParams",
    "PaginatedResponse",
    # ── Clause ─────────────────────────────────────────────────────────────
    "ClauseRecommendation",
    "ClauseResult",
    "ClauseTypeDetection",
    "ClauseConsequence",
    "ClauseSummary",
    "ClausePowerAsymmetry",
    "ClauseCounterOffer",
    "ClausePrecedent",
    "FullClauseAnalysis",
    # ── Contract ───────────────────────────────────────────────────────────
    "ContractCreate",
    "ContractUpdate",
    "ContractRead",
    "ContractListItem",
    "ContractListResponse",
    "ContractAnalysisSummary",
    # ── Scan Job ───────────────────────────────────────────────────────────
    "ScanFeatures",
    "ScanRequest",
    "ScanProgress",
    "ScanJobStatus",
    "ScanResponse",
    "ScanResultSummary",
    "ScanResult",
    # ── Power (Feature 5) ──────────────────────────────────────────────────
    "KeyImbalance",
    "PowerAnalysisResult",
    # ── Precedent (Feature 9) ──────────────────────────────────────────────
    "CaseReference",
    "PrecedentMatch",
    # ── Counter-offer (Feature 6) ──────────────────────────────────────────
    "CounterOfferVersion",
    "CounterOfferResult",
    "CounterOfferStatus",
    # ── Summary + Pros/Cons (Features 4 & 7) ──────────────────────────────
    "SummaryCard",
    "ProsConsItem",
    "ProsConsResult",
    "SummaryResponse",
    # ── Chat (Feature 8) ───────────────────────────────────────────────────
    "ConversationTurn",
    "ChatRequest",
    "ChatResponse",
    # ── Report (Feature 12) ────────────────────────────────────────────────
    "ReportCreate",
    "ReportRead",
    # ── Translation (Feature 11) ───────────────────────────────────────────
    "TranslationRequest",
    "TranslationResponse",
    "SUPPORTED_LANGUAGES",
]