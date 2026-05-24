"""
Contract Analysis Endpoint — POST /api/v1/analyze
Analyzes contract text using the real pipeline and returns structured results.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    contract_text: str
    contract_type: Optional[str] = None  # optional; auto-detected if absent


class ClauseAnalysis(BaseModel):
    text: str
    position_index: int
    risk_level: str                          # SAFE / LOW / MEDIUM / HIGH / CRITICAL
    risk_category: str = "other"
    plain_english: str = ""
    worst_case: str = ""
    financial_exposure: Optional[str] = None
    negotiable: bool = True
    confidence: float = 0.0


class AnalysisResponse(BaseModel):
    clauses: List[ClauseAnalysis]
    contract_type: str = "Unknown"
    overall_risk_score: int = 0
    should_sign: str = "review"
    top_concerns: List[str] = Field(default_factory=list)
    top_positives: List[str] = Field(default_factory=list)
    negotiating_power: str = "Moderate"
    power_score: int = 0
    power_label: str = "Balanced"
    one_liner: str = ""


# ---------------------------------------------------------------------------
# Pipeline imports (lazy to avoid circular imports at module level)
# ---------------------------------------------------------------------------

def _run_pipeline(contract_text: str, contract_type: Optional[str] = None) -> AnalysisResponse:
    """
    Run the full real pipeline on *contract_text* and return an AnalysisResponse.
    """
    import asyncio

    from app.pipelines.type_detection import detect_contract_type
    from app.pipelines.clause_extraction import segment_clauses
    from app.pipelines.risk_classification import run_risk_classification

    # ── Step 1: Detect contract type ────────────────────────────────
    if not contract_type or contract_type == "general":
        type_result = detect_contract_type(contract_text)
        detected_type = type_result.type.value
        logger.info("Detected contract type: %s (conf=%.2f)", detected_type, type_result.confidence)
    else:
        detected_type = contract_type

    # ── Step 2: Extract clauses ─────────────────────────────────────
    raw_clauses = segment_clauses(contract_text)
    clause_texts = [c["text"] for c in raw_clauses]

    if not clause_texts:
        # Fallback: treat the whole text as a single clause
        clause_texts = [contract_text[:2000]]

    logger.info("Extracted %d clauses for analysis", len(clause_texts))

    # ── Step 3: Risk classification (Pass 1 + Pass 2 via LLM) ──────
    user_role = _infer_user_role(detected_type)
    clause_results = run_risk_classification(
        clauses=clause_texts,
        contract_type=detected_type,
        user_role=user_role,
    )

    # ── Step 4: Map ClauseResult → ClauseAnalysis ───────────────────
    analysis_clauses: List[ClauseAnalysis] = []
    clause_map = {c["position_index"]: c["text"] for c in raw_clauses}

    for r in clause_results:
        risk_level = r.risk_severity.value if hasattr(r.risk_severity, "value") else str(r.risk_severity)
        categories = r.risk_categories or ["other"]
        cat = categories[0] if categories else "other"

        analysis_clauses.append(ClauseAnalysis(
            text=clause_map.get(r.clause_index, r.clause_text),
            position_index=r.clause_index,
            risk_level=risk_level,
            risk_category=cat,
            plain_english=r.explanation or "No automated explanation.",
            worst_case=_derive_worst_case(risk_level, cat),
            financial_exposure=_derive_exposure(risk_level, cat),
            negotiable=risk_level in ("MEDIUM", "HIGH", "CRITICAL"),
            confidence=r.confidence_score,
        ))

    # ── Step 5: Derive summary fields ───────────────────────────────
    high_count = sum(1 for c in clause_results if c.risk_severity.value in ("HIGH", "CRITICAL"))
    med_count  = sum(1 for c in clause_results if c.risk_severity.value == "MEDIUM")
    safe_count = sum(1 for c in clause_results if c.risk_severity.value in ("LOW",) and c.safety_rating.value == "SAFE")

    risk_score = _compute_risk_score(high_count, med_count, len(clause_results))
    should_sign = _derive_should_sign(risk_score)
    concerns = [
        c.explanation for c in clause_results
        if c.risk_severity.value in ("HIGH", "CRITICAL")
    ][:5]
    positives = [
        f"Clause {c.clause_index}: {c.explanation}" for c in clause_results
        if c.risk_severity.value == "LOW"
    ][:3] or ["No high-risk clauses detected"]

    power_score = max(0, min(100, 50 - (high_count * 10)))
    if power_score >= 30:
        power_label = "Strong"
        negotiating_power = "Strong"
    elif power_score >= 15:
        power_label = "Balanced"
        negotiating_power = "Moderate"
    else:
        power_label = "Weak"
        negotiating_power = "Weak"

    return AnalysisResponse(
        clauses=analysis_clauses,
        contract_type=detected_type,
        overall_risk_score=risk_score,
        should_sign=should_sign,
        top_concerns=concerns if concerns else ["Review all clauses with legal counsel"],
        top_positives=positives,
        negotiating_power=negotiating_power,
        power_score=power_score,
        power_label=power_label,
        one_liner=_derive_one_liner(detected_type, risk_score, high_count, safe_count),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLASSIFICATION_KEYWORDS = {
    "Employment": "employee",
    "NDA": "receiving party",
    "Service Agreement": "service provider",
    "Vendor": "vendor",
    "SaaS": "subscriber",
    "Lease": "tenant",
    "Partnership": "partner",
    "Loan": "borrower",
    "IP Assignment": "assignor",
    "Settlement": "claimant",
}


def _infer_user_role(contract_type: str) -> str:
    for key, role in _CLASSIFICATION_KEYWORDS.items():
        if key.lower() in contract_type.lower() or contract_type.lower() in key.lower():
            return role
    return "reviewing party"


def _derive_worst_case(risk_level: str, category: str) -> str:
    """Derive a worst-case description from risk level + category."""
    if risk_level in ("HIGH", "CRITICAL"):
        mapping = {
            "indemnity": "Unlimited financial liability for claims and damages",
            "non_compete": "Inability to work in your industry for extended period",
            "ip_assignment": "Loss of ownership over your own intellectual property",
            "non_solicitation": "Restrictions on working with clients and employees",
            "payment": "Unexpected payment obligations or clawbacks",
            "arbitration_only": "Loss of right to sue in court; forced into private arbitration",
            "unilateral_modification": "Terms may change without your consent at any time",
            "liquidated_damages": "Disproportionate penalties for breach",
            "termination_for_convenience": "Contract may be terminated without cause or notice",
            "limitation_of_liability": "Limited recourse if the other party causes harm",
            "auto_renewal": "Contract auto-renews; you may forget to cancel",
        }
        return mapping.get(category, "Significant legal or financial risk")
    if risk_level == "MEDIUM":
        return "Moderate risk — review with legal counsel"
    return "Low risk — standard contractual provision"


def _derive_exposure(risk_level: str, category: str) -> Optional[str]:
    if risk_level == "HIGH":
        return "Significant"
    if risk_level == "CRITICAL":
        return "Critical"
    if risk_level == "MEDIUM":
        return "Moderate"
    return None


def _compute_risk_score(high: int, med: int, total: int) -> int:
    if total == 0:
        return 0
    score = int((high * 35 + med * 15) / max(1, total))
    return min(100, score)


def _derive_should_sign(risk_score: int) -> str:
    if risk_score <= 15:
        return "yes_as_is"
    if risk_score <= 45:
        return "yes_with_changes"
    if risk_score <= 70:
        return "review"
    return "no"


def _derive_one_liner(contract_type: str, risk_score: int, high: int, safe: int) -> str:
    if high == 0:
        return f"{contract_type} — {safe} safe clauses, overall risk score {risk_score}/100"
    return f"{contract_type} — {high} high-risk clause(s) identified, overall risk score {risk_score}/100. Recommend {'signing with changes' if risk_score < 50 else 'further review'}."


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def analyze_contract(request: AnalyzeRequest):
    """
    Analyze a contract using the real AI pipeline.
    """
    try:
        result = _run_pipeline(request.contract_text, request.contract_type)
        return result.model_dump()
    except Exception as exc:
        logger.exception("Pipeline analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")


# Alias for compatibility
router.add_api_route("/analyze", analyze_contract, methods=["POST"])
