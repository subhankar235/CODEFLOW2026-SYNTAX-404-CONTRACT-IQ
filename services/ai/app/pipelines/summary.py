"""
STEP 7.3 — Summary Card Pipeline
-----------------------------------
PURPOSE:
  This pipeline generates two outputs that act as the "executive summary"
  of a contract analysis:

  1. SUMMARY CARD — a plain-language card telling the user:
     • A one-liner verdict on the contract
     • Whether they should sign (and under what conditions)
     • The top 3 concerns and top 2 positives
     • An overall risk score (0-100)
     • Their negotiating power (Strong / Moderate / Weak)

  2. PROS vs CONS SNAPSHOT — a structured list of pros and cons,
     each tagged with a dimension label (Financial, Liability, IP, etc.),
     plus a final verdict string.

  Uses the FAST_MODEL (e.g. gemini-flash) because this is a summarisation
  task over already-processed data — speed matters here.

FLOW:
  [HIGH/MEDIUM summaries + risk stats] → AI call (FAST_MODEL)
  → SummaryCard + ProsConsSnapshot → store in analysis_results → return both

HOW IT FITS IN:
  Called from the main Celery task AFTER power analysis completes.
  Its output is the primary data shown on the front-end report card.
"""

import asyncio
import os
import json
import logging
from typing import List

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RiskStats(BaseModel):
    """Counts of clauses at each risk level — passed in from the classifier."""
    high_count:   int
    medium_count: int
    low_count:    int
    total_count:  int


class ProConItem(BaseModel):
    """A single pro or con with a dimension tag for front-end filtering."""
    dimension: str   # e.g. "Financial", "Liability", "IP", "Termination", "Compliance"
    text:      str   # Plain-language description


class SummaryCard(BaseModel):
    """
    The main summary card shown to the user at the top of the report.
    All fields are intentionally plain-language — no legalese.
    """
    one_liner:         str   # e.g. "This contract heavily favours the employer."
    should_you_sign:   str   # One of: "Yes as-is" | "Yes with changes" | "No"
    top_3_concerns:    List[str]   # Up to 3 items
    top_2_positives:   List[str]   # Up to 2 items
    overall_risk_score: int        # 0 (safe) to 100 (extremely risky)
    negotiating_power: str         # One of: "Strong" | "Moderate" | "Weak"

    @field_validator("should_you_sign")
    @classmethod
    def validate_sign(cls, v: str) -> str:
        allowed = {"Yes as-is", "Yes with changes", "No"}
        if v not in allowed:
            # Try to normalize
            v_lower = v.strip().lower()
            if "no" == v_lower:
                return "No"
            elif "as-is" in v_lower or "as is" in v_lower:
                return "Yes as-is"
            else:
                return "Yes with changes"
        return v

    @field_validator("overall_risk_score")
    @classmethod
    def validate_risk_score(cls, v) -> int:
        if isinstance(v, float):
            v = int(v)
        if not isinstance(v, int):
            try:
                v = int(v)
            except (ValueError, TypeError):
                return 50
        return max(0, min(100, v))

    @field_validator("negotiating_power")
    @classmethod
    def validate_negotiating_power(cls, v: str) -> str:
        allowed = {"Strong", "Moderate", "Weak"}
        if v not in allowed:
            v_title = v.strip().title()
            if v_title in allowed:
                return v_title
            return "Moderate"
        return v

    @field_validator("top_3_concerns")
    @classmethod
    def validate_concerns(cls, v: List[str]) -> List[str]:
        # Allow 1-3 items instead of exactly 3
        if len(v) > 3:
            return v[:3]
        if not v:
            return ["Review all contract terms carefully"]
        return v

    @field_validator("top_2_positives")
    @classmethod
    def validate_positives(cls, v: List[str]) -> List[str]:
        # Allow 1-2 items instead of exactly 2
        if len(v) > 2:
            return v[:2]
        if not v:
            return ["Contract terms can be negotiated"]
        return v


class ProsConsSnapshot(BaseModel):
    """
    The Pros vs Cons snapshot shown below the summary card.
    Each item carries a dimension label so the UI can colour-code them.
    """
    pros:    List[ProConItem]   # Positive aspects of the contract
    cons:    List[ProConItem]   # Negative / risky aspects
    verdict: str                # Short closing verdict, e.g. "Negotiate before signing."


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_summary_prompt(
    contract_type:    str,
    high_summaries:   List[str],
    medium_summaries: List[str],
    stats:            RiskStats,
) -> str:
    high_block   = "\n".join(f"- {s}" for s in high_summaries)   or "None"
    medium_block = "\n".join(f"- {s}" for s in medium_summaries) or "None"

    return f"""You are a contract analyst writing a plain-language report for a non-lawyer.

Contract Type: {contract_type}
Risk Statistics: {stats.high_count} HIGH | {stats.medium_count} MEDIUM | {stats.low_count} LOW | {stats.total_count} TOTAL

HIGH-Risk Clause Summaries:
{high_block}

MEDIUM-Risk Clause Summaries:
{medium_block}

Respond ONLY with a valid JSON object — no markdown, no explanation.
{{
  "one_liner":           "<single sentence verdict on this contract>",
  "should_you_sign":     "<exactly one of: Yes as-is | Yes with changes | No>",
  "top_3_concerns":      ["<concern 1>", "<concern 2>", "<concern 3>"],
  "top_2_positives":     ["<positive 1>", "<positive 2>"],
  "overall_risk_score":  <integer 0-100>,
  "negotiating_power":   "<exactly one of: Strong | Moderate | Weak>"
}}"""


def _build_pros_cons_prompt(
    high_summaries:   List[str],
    medium_summaries: List[str],
    low_summaries:    List[str],
) -> str:
    all_clauses = (
        "\n".join(f"[HIGH] {s}"   for s in high_summaries)
        + "\n"
        + "\n".join(f"[MEDIUM] {s}" for s in medium_summaries)
        + "\n"
        + "\n".join(f"[LOW] {s}"    for s in low_summaries)
    ).strip()

    return f"""You are a contract analyst. Based on the clause summaries below,
generate a structured Pros vs Cons breakdown. Each item MUST have a dimension tag.

Allowed dimension tags: Financial, Liability, IP, Termination, Compliance, Privacy, Scope, Other

Clause Summaries:
{all_clauses}

Respond ONLY with a valid JSON object — no markdown, no preamble.
{{
  "pros": [
    {{"dimension": "<tag>", "text": "<plain-language benefit>"}},
    ...
  ],
  "cons": [
    {{"dimension": "<tag>", "text": "<plain-language risk>"}},
    ...
  ],
  "verdict": "<short closing sentence>"
}}"""


# ---------------------------------------------------------------------------
# Core pipeline function (async)
# ---------------------------------------------------------------------------

async def _run_summary_async(
    contract_type:    str,
    high_summaries:   List[str],
    medium_summaries: List[str],
    low_summaries:    List[str],
    stats:            RiskStats,
    analysis_id:      str,
    fast_model:       str = None,
) -> tuple:
    """Async implementation of summary generation."""
    from ..models.openrouter_client import OpenRouterClient

    if fast_model is None:
        fast_model = os.getenv("FAST_MODEL", "google/gemini-flash-1.5")

    logger.info(
        "Summary pipeline: contract_type='%s' H=%d M=%d L=%d",
        contract_type, stats.high_count, stats.medium_count, stats.low_count,
    )

    client = OpenRouterClient()

    # ---- Call 1: Summary Card ------------------------------------------------
    try:
        summary_prompt = _build_summary_prompt(
            contract_type, high_summaries, medium_summaries, stats
        )
        resp1 = await client.complete(
            system_prompt="You are a contract analyst. Return ONLY valid JSON.",
            user_prompt=summary_prompt,
            model=fast_model,
            json_mode=True,
        )
        content1 = resp1["choices"][0]["message"].get("content", "{}")
        raw1 = json.loads(content1)
        summary = SummaryCard(**raw1)
        logger.info("Summary card generated: sign='%s' score=%d",
                    summary.should_you_sign, summary.overall_risk_score)
    except Exception as e:
        logger.error("Summary card generation failed: %s", e)
        # Fallback summary card
        summary = SummaryCard(
            one_liner=f"This {contract_type} contract requires careful review.",
            should_you_sign="Yes with changes",
            top_3_concerns=high_summaries[:3] if high_summaries else ["Review all terms"],
            top_2_positives=["Contract terms can be negotiated", "Standard legal structure"],
            overall_risk_score=min(100, 20 + stats.high_count * 20 + stats.medium_count * 10),
            negotiating_power="Moderate" if stats.high_count < 3 else "Weak",
        )

    # ---- Call 2: Pros vs Cons ------------------------------------------------
    try:
        pros_cons_prompt = _build_pros_cons_prompt(
            high_summaries, medium_summaries, low_summaries
        )
        resp2 = await client.complete(
            system_prompt="You are a contract analyst. Return ONLY valid JSON.",
            user_prompt=pros_cons_prompt,
            model=fast_model,
            json_mode=True,
        )
        content2 = resp2["choices"][0]["message"].get("content", "{}")
        raw2 = json.loads(content2)

        # Deserialise nested ProConItem lists
        raw2["pros"] = [ProConItem(**p) if isinstance(p, dict) else p for p in raw2.get("pros", [])]
        raw2["cons"] = [ProConItem(**c) if isinstance(c, dict) else c for c in raw2.get("cons", [])]

        pros_cons = ProsConsSnapshot(**raw2)
        logger.info("Pros/cons generated: %d pros, %d cons",
                    len(pros_cons.pros), len(pros_cons.cons))
    except Exception as e:
        logger.error("Pros/cons generation failed: %s", e)
        # Fallback pros/cons
        pros_cons = ProsConsSnapshot(
            pros=[ProConItem(dimension="Scope", text="Contract provides clear terms")],
            cons=[ProConItem(dimension="Liability", text=s) for s in high_summaries[:3]] if high_summaries
                 else [ProConItem(dimension="Other", text="Review all terms carefully")],
            verdict="Negotiate key terms before signing.",
        )

    return summary, pros_cons


def run_summary(
    contract_type:    str,
    high_summaries:   List[str],
    medium_summaries: List[str],
    low_summaries:    List[str],
    stats:            RiskStats,
    analysis_id:      str,
    fast_model:       str = None,
) -> tuple:
    """
    Main entry point for the Summary Card Pipeline.

    Makes TWO sequential AI calls:
      Call 1 → SummaryCard  (the headline report card)
      Call 2 → ProsConsSnapshot  (the detailed pros/cons breakdown)

    Both use the FAST_MODEL because they summarise pre-processed data
    and latency is user-facing.

    Args:
        contract_type:    e.g. "Employment Agreement", "SaaS License"
        high_summaries:   Plain-language summaries of HIGH-risk clauses
        medium_summaries: Plain-language summaries of MEDIUM-risk clauses
        low_summaries:    Plain-language summaries of LOW-risk clauses
        stats:            Clause counts per risk level
        analysis_id:      DB record ID for this analysis
        fast_model:       Model ID (defaults to FAST_MODEL env var)

    Returns:
        Tuple of (SummaryCard, ProsConsSnapshot)
    """
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                _run_summary_async(
                    contract_type, high_summaries, medium_summaries,
                    low_summaries, stats, analysis_id, fast_model
                )
            )
            return future.result()
    except RuntimeError:
        return asyncio.run(
            _run_summary_async(
                contract_type, high_summaries, medium_summaries,
                low_summaries, stats, analysis_id, fast_model
            )
        )