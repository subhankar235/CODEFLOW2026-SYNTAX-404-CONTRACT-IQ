"""
STEP 7.2 — Power Asymmetry Pipeline
-------------------------------------
PURPOSE:
  This pipeline scores the "power imbalance" of an entire contract.
  Rather than looking at individual clauses, it takes the FULL picture
  (all clause results + their risk assessments) and produces a single
  integer score from -100 to +100:
      -100  = entirely one-sided against the user
         0  = perfectly balanced
      +100  = entirely in the user's favour

  It also surfaces key imbalances (specific problematic areas) and
  leverage points (what the user could negotiate on).

FLOW:
  [All Clause Results] → single AI call → parse PowerAsymmetryResult
  → store in analysis_results table → return result

HOW IT FITS IN:
  Called from the main Celery task AFTER consequence generation completes.
  Its output is stored to DB and also forwarded to the summary pipeline.
"""

import asyncio
import os
import json
import logging
from typing import List, Optional

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ClauseResultInput(BaseModel):
    """
    Lightweight view of a clause result that this pipeline needs.
    The caller assembles this from the risk classification output.
    """
    clause_id:     str
    clause_type:   str
    clause_text:   str
    risk_level:    str   # "HIGH", "MEDIUM", "LOW"
    risk_category: str   # e.g. "Financial", "IP", "Liability"
    summary:       Optional[str] = None  # AI-generated plain-language summary


class KeyImbalance(BaseModel):
    """Represents one identified power imbalance in the contract."""
    area:        str   # e.g. "Termination Rights", "Liability Cap"
    description: str   # Plain-language explanation of why this is one-sided
    favors:      str   # "counterparty" or "user"


class PowerAsymmetryResult(BaseModel):
    """
    Full power asymmetry analysis for a contract.
    Stored to the analysis_results table after generation.
    """
    power_score:     int            # -100 to +100
    power_label:     str            # e.g. "Heavily Unfavourable", "Balanced", "Favourable"
    key_imbalances:  List[KeyImbalance]  # At least 1 for contracts with HIGH-risk clauses
    leverage_points: List[str]      # What the user can push back on during negotiation

    @field_validator("power_score")
    @classmethod
    def validate_power_score(cls, v) -> int:
        if isinstance(v, float):
            v = int(v)
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                return 0
        return max(-100, min(100, v))

    @field_validator("key_imbalances")
    @classmethod
    def validate_imbalances(cls, v: List[KeyImbalance]) -> List[KeyImbalance]:
        return v


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_power_asymmetry_prompt(
    clauses:   List[ClauseResultInput],
    user_role: str,
) -> str:
    """
    Builds the power_asymmetry.txt prompt by injecting clause data and user role.
    """
    clause_block = "\n\n".join(
        f"Clause {i+1} [{c.risk_level}] — {c.clause_type} ({c.risk_category}):\n{c.clause_text}"
        for i, c in enumerate(clauses)
    )

    return f"""You are an expert contract negotiation analyst. Assess the overall power
balance of this contract from the perspective of: {user_role}.

Analyze ALL clauses below holistically — consider which party has more rights,
fewer obligations, broader escape clauses, and stronger enforcement mechanisms.

CONTRACT CLAUSES:
{clause_block}

Respond ONLY with a valid JSON object — no markdown, no preamble.
Use this exact schema:
{{
  "power_score":     <integer from -100 (worst for user) to +100 (best for user)>,
  "power_label":     "<one of: Heavily Unfavourable | Unfavourable | Slightly Unfavourable | Balanced | Slightly Favourable | Favourable | Heavily Favourable>",
  "key_imbalances":  [
    {{
      "area":        "<contract area, e.g. Termination Rights>",
      "description": "<plain-language explanation>",
      "favors":      "<counterparty | user>"
    }}
  ],
  "leverage_points": [
    "<specific clause or right the user could negotiate>",
    ...
  ]
}}"""


# ---------------------------------------------------------------------------
# Core pipeline function (async)
# ---------------------------------------------------------------------------

async def _run_power_asymmetry_async(
    clauses: List[ClauseResultInput],
    user_role: str,
    analysis_id: str,
    primary_model: str = None,
) -> PowerAsymmetryResult:
    """Async implementation of power asymmetry analysis."""
    from ..models.openrouter_client import OpenRouterClient

    if primary_model is None:
        primary_model = os.getenv("PRIMARY_MODEL", "meta-llama/llama-3.3-70b-instruct")

    logger.info(
        "Power asymmetry pipeline: analyzing %d clauses for role='%s'",
        len(clauses), user_role,
    )

    client = OpenRouterClient()
    prompt = _build_power_asymmetry_prompt(clauses, user_role)

    try:
        # Single AI call for the whole contract (holistic analysis)
        response = await client.complete(
            system_prompt="You are a contract negotiation expert. Return ONLY valid JSON.",
            user_prompt=prompt,
            model=primary_model,
            json_mode=False,
        )

        content = response["choices"][0]["message"].get("content", "{}")
        raw_json = json.loads(content)

        # Deserialise nested key_imbalances list
        raw_imbalances = raw_json.get("key_imbalances", [])
        if isinstance(raw_imbalances, list):
            raw_json["key_imbalances"] = [
                KeyImbalance(**item) if isinstance(item, dict) else item
                for item in raw_imbalances
            ]

        result = PowerAsymmetryResult(**raw_json)

        # Extra business rule: HIGH-risk contracts must have ≥1 key imbalance
        high_risk_count = sum(1 for c in clauses if c.risk_level == "HIGH")
        if high_risk_count > 0 and len(result.key_imbalances) == 0:
            logger.warning(
                "Contract has %d HIGH-risk clauses but 0 key_imbalances returned.",
                high_risk_count,
            )

        logger.info(
            "Power asymmetry complete: score=%d label='%s' imbalances=%d",
            result.power_score, result.power_label, len(result.key_imbalances),
        )
        return result

    except Exception as e:
        logger.error("Power asymmetry pipeline failed: %s", e)
        # Return a fallback result
        high_count = sum(1 for c in clauses if c.risk_level == "HIGH")
        med_count = sum(1 for c in clauses if c.risk_level == "MEDIUM")
        
        fallback_score = max(-80, -10 * high_count - 5 * med_count)
        if high_count >= 3:
            label = "Heavily Unfavourable"
        elif high_count >= 1:
            label = "Unfavourable"
        elif med_count >= 3:
            label = "Slightly Unfavourable"
        else:
            label = "Balanced"
        
        return PowerAsymmetryResult(
            power_score=fallback_score,
            power_label=label,
            key_imbalances=[],
            leverage_points=["Negotiate key terms with legal counsel"],
        )


def run_power_asymmetry(
    clauses: List[ClauseResultInput],
    user_role: str,
    analysis_id: str,
    primary_model: str = None,
) -> PowerAsymmetryResult:
    """
    Main entry point for the Power Asymmetry Pipeline.

    Steps:
      1. Build a comprehensive prompt using all clause results.
      2. Send a single AI model call to score the full contract.
      3. Parse and validate the response into a PowerAsymmetryResult.
      4. Return the result for use in downstream pipelines.

    Args:
        clauses:       All clause results (all risk levels included for full context).
        user_role:     The user's role, e.g. "employee", "vendor", "contractor".
        analysis_id:   The DB record ID for this analysis (used for storage).
        primary_model: OpenRouter model ID.

    Returns:
        PowerAsymmetryResult — the complete power asymmetry analysis.
    """
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                _run_power_asymmetry_async(clauses, user_role, analysis_id, primary_model)
            )
            return future.result()
    except RuntimeError:
        return asyncio.run(
            _run_power_asymmetry_async(clauses, user_role, analysis_id, primary_model)
        )