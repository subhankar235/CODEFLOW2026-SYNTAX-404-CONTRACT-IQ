"""
Step 6.3 — Risk Classification Pipeline
Two-pass pipeline:
  Pass 1 — rule engine triages every clause into GREEN / YELLOW / RED
  Pass 2 — LLM analyses only YELLOW and RED clauses, in batches of <=20
GREEN clauses receive default LOW/SAFE results without any LLM call.
The streaming variant yields ClauseResult objects one at a time.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..rules.risk_mapper import (
    ClauseTriage,
    TriageLevel,
    partition_by_triage,
    triage_clauses,
)
from ..utils.prompt_loader import load_prompt_split, split_system_user

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "meta-llama/llama-3.3-70b-instruct")
MAX_BATCH_SIZE = 20

# Regex to strip markdown fences from LLM output
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------

class RiskSeverity(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class SafetyRating(str, Enum):
    SAFE    = "SAFE"
    CAUTION = "CAUTION"
    DANGER  = "DANGER"


class ClauseResult(BaseModel):
    """Full analysis result for a single clause."""

    clause_index: int
    clause_text: str
    triage: str
    risk_severity: RiskSeverity = RiskSeverity.LOW
    safety_rating: SafetyRating = SafetyRating.SAFE
    risk_categories: List[str] = Field(default_factory=list)
    explanation: str = ""
    recommendation: str = ""
    problematic_language: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    power_imbalance: Optional[str] = None
    llm_analysed: bool = False

    @field_validator("risk_severity", mode="before")
    @classmethod
    def _coerce_severity(cls, v: Any) -> str:
        if isinstance(v, RiskSeverity):
            return v
        return str(v).upper()

    @field_validator("safety_rating", mode="before")
    @classmethod
    def _coerce_safety(cls, v: Any) -> str:
        if isinstance(v, SafetyRating):
            return v
        return str(v).upper()


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _load_risk_prompt(
    contract_type: str,
    user_role: str,
    batch_size: int,
) -> tuple[str, str]:
    """Load risk_analysis.txt, substitute shared vars, adapt for batch mode.

    Returns
    -------
    (system_prompt, user_template) — the user_template still has
    ``{{position_index}}`` and ``{{clause_text}}`` placeholders per clause.
    """
    # Read raw template and split, bypassing strict placeholder checking
    from ..utils.prompt_loader import split_system_user
    from ..utils.prompt_loader import _read_template, _resolve_path

    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    file_path = _resolve_path("risk_analysis", prompts_dir)
    raw = _read_template(str(file_path))
    raw_system, raw_user = split_system_user(raw)

    # Substitute shared vars into the system prompt
    system_prompt = (
        raw_system.replace("{{contract_type}}", contract_type)
        .replace("{{party_role}}", user_role)
    )

    # Adapt system prompt for multi-clause batch analysis.
    # The json_object response format requires a single JSON object,
    # so we wrap the array in a ``clauses`` key.
    system_prompt += (
        f"\n\nYou will receive {batch_size} clause(s) separated by '---'. "
        "Analyse EACH clause independently. Return a JSON object with a "
        "single key 'clauses' whose value is an array of results, one per clause. "
        "Each result object must have an 'index' field matching the EXACT 'position X' number provided for that clause, plus:\n"
        '  "risk_severity": one of LOW, MEDIUM, HIGH, CRITICAL\n'
        '  "safety_rating": one of SAFE, CAUTION, DANGER\n'
        '  "risk_categories": array of strings (e.g. ["indemnity", "ip_assignment"])\n'
        '  "explanation": 1-2 sentence explanation of the risk\n'
        '  "recommendation": 1 sentence actionable recommendation\n'
        '  "problematic_language": exact quote from the clause or null\n'
        '  "confidence_score": float 0.0-1.0\n'
        "Return ONLY the JSON object. No markdown, no preamble."
    )

    return system_prompt, raw_user


def _render_user_prompt(
    template: str,
    ct: ClauseTriage,
    contract_type: str,
    user_role: str,
) -> str:
    """Render the user prompt for a single clause with placeholders filled."""
    return (
        template.replace("{{position_index}}", str(ct.index))
        .replace("{{clause_text}}", ct.text)
        .replace("{{contract_type}}", contract_type)
        .replace("{{party_role}}", user_role)
    )


# ---------------------------------------------------------------------------
# LLM response parsing
# ---------------------------------------------------------------------------

def _parse_llm_response(
    raw: str,
    batch: List[ClauseTriage],
) -> List[ClauseResult]:
    """Parse the LLM JSON response and merge with ClauseTriage data.

    Handles both raw arrays and ``{"clauses": [...]}`` wrapping.
    Falls back gracefully on parse errors.
    """
    cleaned = raw.strip()
    match = re.search(r"```(?:json)?(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    else:
        start_obj = cleaned.find("{")
        start_arr = cleaned.find("[")
        if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
            end_obj = cleaned.rfind("}")
            if end_obj != -1:
                cleaned = cleaned[start_obj:end_obj+1]
        elif start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
            end_arr = cleaned.rfind("]")
            if end_arr != -1:
                cleaned = cleaned[start_arr:end_arr+1]

    if not cleaned:
        logger.warning("LLM JSON parse error: LLM returned an empty response.")
        return _fallback_results(batch)

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("LLM JSON parse error: %s", exc)
        return _fallback_results(batch)

    # Unwrap dict → extract the clauses array
    if isinstance(payload, dict):
        for key in ("clauses", "results", "data", "analysis"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
        else:
            logger.warning("No array key found in LLM dict response; keys=%s", list(payload.keys()))
            return _fallback_results(batch)

    if not isinstance(payload, list):
        logger.warning("LLM response not a list after unwrapping; got %s", type(payload).__name__)
        return _fallback_results(batch)

    batch_by_index = {ct.index: ct for ct in batch}
    results: List[ClauseResult] = []

    for item in payload:
        idx = item.get("index")
        if idx is None:
            continue
        ct = batch_by_index.get(idx)
        if ct is None:
            logger.warning("LLM returned unknown index %s; skipping", idx)
            continue

        try:
            # Map LLM response fields→ClauseResult fields
            severity_str = str(
                item.get("risk_severity") or item.get("risk_level", "MEDIUM")
            ).upper()
            severity_str = severity_str if severity_str in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"

            safety_str = str(
                item.get("safety_rating") or _derive_safety(severity_str)
            ).upper()
            safety_str = safety_str if safety_str in {"SAFE", "CAUTION", "DANGER"} else "CAUTION"

            explanation = (
                item.get("explanation")
                or item.get("risk_explanation")
                or item.get("risk_summary")
                or ""
            )
            recommendation = (
                item.get("recommendation")
                or (item.get("recommendations") or [""])[0]
                or ""
            )
            categories_raw = (
                item.get("risk_categories")
                or ([item["risk_category"]] if item.get("risk_category") else [])
                or ct.result.categories
            )
            if isinstance(categories_raw, str):
                categories_raw = [categories_raw]

            result = ClauseResult(
                clause_index=ct.index,
                clause_text=ct.text,
                triage=ct.result.triage.value,
                risk_severity=RiskSeverity(severity_str),
                safety_rating=SafetyRating(safety_str),
                risk_categories=[str(c) for c in categories_raw],
                explanation=str(explanation),
                recommendation=str(recommendation),
                problematic_language=item.get("problematic_language"),
                confidence_score=float(item.get("confidence_score", 0.0)),
                llm_analysed=True,
            )
        except Exception as exc:
            logger.warning("Pydantic validation failed for idx %s (%s); fallback", idx, exc)
            result = _fallback_single(ct)

        results.append(result)

    # Ensure every clause in the batch has a result
    returned_indices = {r.clause_index for r in results}
    for ct in batch:
        if ct.index not in returned_indices:
            results.append(_fallback_single(ct))

    return results


def _derive_safety(severity: str) -> str:
    mapping = {"LOW": "SAFE", "MEDIUM": "CAUTION", "HIGH": "DANGER", "CRITICAL": "DANGER"}
    return mapping.get(severity, "CAUTION")


def _fallback_results(batch: List[ClauseTriage]) -> List[ClauseResult]:
    return [_fallback_single(ct) for ct in batch]


def _fallback_single(ct: ClauseTriage) -> ClauseResult:
    severity = RiskSeverity.HIGH if ct.result.triage == TriageLevel.RED else RiskSeverity.MEDIUM
    rating = SafetyRating.DANGER if ct.result.triage == TriageLevel.RED else SafetyRating.CAUTION
    return ClauseResult(
        clause_index=ct.index,
        clause_text=ct.text,
        triage=ct.result.triage.value,
        risk_severity=severity,
        safety_rating=rating,
        risk_categories=ct.result.categories,
        explanation="Automated fallback — manual review recommended.",
        recommendation="Review with legal counsel.",
        confidence_score=0.0,
        llm_analysed=False,
    )


def _green_result(ct: ClauseTriage) -> ClauseResult:
    return ClauseResult(
        clause_index=ct.index,
        clause_text=ct.text,
        triage=TriageLevel.GREEN.value,
        risk_severity=RiskSeverity.LOW,
        safety_rating=SafetyRating.SAFE,
        risk_categories=[],
        explanation="No risk signals detected.",
        recommendation="No action required.",
        confidence_score=1.0,
        llm_analysed=False,
    )


# ---------------------------------------------------------------------------
# Batch splitter
# ---------------------------------------------------------------------------

def _batch(items: List[ClauseTriage], size: int) -> List[List[ClauseTriage]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# Single-batch LLM call with retry
# ---------------------------------------------------------------------------

async def _call_llm_batch_async(
    client: Any,
    batch: List[ClauseTriage],
    contract_type: str,
    user_role: str,
    retry: bool = True,
) -> List[ClauseResult]:
    """Analyse a single clause batch via LLM, with one retry on failure."""
    system_prompt, user_template = _load_risk_prompt(
        contract_type, user_role, len(batch)
    )

    # Render user prompt for each clause
    clause_prompts = [
        _render_user_prompt(user_template, ct, contract_type, user_role)
        for ct in batch
    ]
    user_prompt = "\n\n---\n\n".join(clause_prompts)

    try:
        raw_response = await client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=PRIMARY_MODEL,
<<<<<<< HEAD
            json_mode=False,
=======
            json_mode=True,
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
        )
        content = raw_response["choices"][0]["message"].get("content", "") or ""
        parsed = _parse_llm_response(content, batch)

        # Check: did all clauses get valid LLM analysis?
        non_green = [r for r in parsed if r.triage != "GREEN"]
        if all(r.llm_analysed for r in non_green):
            return parsed

        failed = [r.clause_index for r in parsed if not r.llm_analysed and r.triage != "GREEN"]
        if retry and failed:
            logger.info(
                "Retrying batch due to %d failed clause(s): %s",
                len(failed), failed,
            )
            return await _call_llm_batch_async(
                client, batch, contract_type, user_role, retry=False
            )

        return parsed

    except Exception as exc:
        logger.error("LLM batch call failed: %s", exc)
        if retry:
            logger.info("Retrying batch after error")
            try:
                return await _call_llm_batch_async(
                    client, batch, contract_type, user_role, retry=False
                )
            except Exception:
                pass
        return _fallback_results(batch)


# ---------------------------------------------------------------------------
# Synchronous pipeline
# ---------------------------------------------------------------------------

def run_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    openrouter_client=None,
    call_counter: Optional[list] = None,
) -> List[ClauseResult]:
    """
    Full two-pass risk classification (blocking / synchronous).

    Parameters
    ----------
    clauses:        Ordered list of clause text strings.
    contract_type:  Detected contract type (e.g. "Employment").
    user_role:      Reviewing party role (e.g. "employee").
    openrouter_client: An OpenRouterClient instance (optional).
    call_counter:   If provided, a list that receives the number of LLM calls
                    made (useful for verification).

    Returns
    -------
    List[ClauseResult] in clause index order.
    """
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                _run_risk_classification_async(
                    clauses, contract_type, user_role,
                    openrouter_client, call_counter,
                ),
            )
            return future.result()
    except RuntimeError:
        return asyncio.run(
            _run_risk_classification_async(
                clauses, contract_type, user_role,
                openrouter_client, call_counter,
            ),
        )


async def _run_risk_classification_async(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    openrouter_client=None,
    call_counter: Optional[list] = None,
) -> List[ClauseResult]:
    """Internal async implementation of the two-pass pipeline."""
    from ..models.openrouter_client import OpenRouterClient

    client: Any = openrouter_client or OpenRouterClient()
    llm_calls = 0

    # ── Pass 1: Rule engine triage ─────────────────────────────────────
    triaged = triage_clauses(clauses)
    buckets = partition_by_triage(triaged)

    green_results: List[ClauseResult] = [
        _green_result(ct) for ct in buckets[TriageLevel.GREEN.value]
    ]
    flagged = (
        buckets[TriageLevel.YELLOW.value]
        + buckets[TriageLevel.RED.value]
    )

    logger.info(
        "Risk classification: %d GREEN (skip LLM), %d flagged (YELLOW+RED)",
        len(green_results), len(flagged),
    )

    # ── Pass 2: LLM analysis of flagged clauses in batches ────────────
    llm_results: List[ClauseResult] = []
    for batch_items in _batch(flagged, MAX_BATCH_SIZE):
        logger.info(
            "Sending batch of %d clauses to LLM (indices %s-%s)",
            len(batch_items), batch_items[0].index, batch_items[-1].index,
        )
        batch_results = await _call_llm_batch_async(
            client, batch_items, contract_type, user_role,
        )
        llm_results.extend(batch_results)
        llm_calls += 1

    if call_counter is not None:
        call_counter.append(llm_calls)

    # ── Merge and sort by original clause index ───────────────────────
    all_results = green_results + llm_results
    all_results.sort(key=lambda r: r.clause_index)
    return all_results


# ---------------------------------------------------------------------------
# Streaming pipeline
# ---------------------------------------------------------------------------

def stream_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    openrouter_client=None,
) -> Iterator[ClauseResult]:
    """Streaming synchronous variant.

    Yields ClauseResult objects one at a time.
    GREEN clauses are yielded immediately (before any LLM call).
    YELLOW/RED clauses are yielded per-batch as each batch completes.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                _collect_streaming_results(
                    clauses, contract_type, user_role, openrouter_client,
                ),
            )
            for r in future.result():
                yield r
    else:
        results = asyncio.run(
            _collect_streaming_results(
                clauses, contract_type, user_role, openrouter_client,
            ),
        )
        for r in results:
            yield r


async def _collect_streaming_results(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    openrouter_client=None,
) -> List[ClauseResult]:
    """Collect all streaming results into a list."""
    results: List[ClauseResult] = []
    async for r in async_stream_risk_classification(
        clauses, contract_type, user_role, openrouter_client,
    ):
        results.append(r)
    return results


async def async_stream_risk_classification(
    clauses: List[str],
    contract_type: str,
    user_role: str,
    openrouter_client=None,
    call_counter: Optional[list] = None,
) -> AsyncIterator[ClauseResult]:
    """Async streaming variant for use in FastAPI / asyncio contexts.

    Yields GREEN clauses immediately, then yields YELLOW/RED results
    one at a time as each batch completes.
    """
    from ..models.openrouter_client import OpenRouterClient

    client: Any = openrouter_client or OpenRouterClient()
    llm_calls = 0

    triaged = triage_clauses(clauses)
    buckets = partition_by_triage(triaged)

    # Yield GREEN results immediately (no LLM call)
    for ct in buckets[TriageLevel.GREEN.value]:
        yield _green_result(ct)

    flagged = (
        buckets[TriageLevel.YELLOW.value]
        + buckets[TriageLevel.RED.value]
    )

    for batch_items in _batch(flagged, MAX_BATCH_SIZE):
        try:
            batch_results = await _call_llm_batch_async(
                client, batch_items, contract_type, user_role,
            )
            llm_calls += 1
            for clause_result in batch_results:
                yield clause_result
        except Exception as exc:
            logger.error("Batch LLM call failed: %s; using fallbacks", exc)
            for ct in batch_items:
                yield _fallback_single(ct)

    if call_counter is not None:
        call_counter.append(llm_calls)
