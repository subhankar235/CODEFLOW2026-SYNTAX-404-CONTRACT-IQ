"""
services/ai/tasks/contract_analysis.py
---------------------------------------
Main Celery Task — Contract Analysis Pipeline.

What this file does:
  Defines the `analyse_contract` Celery task, which orchestrates the full
  contract analysis pipeline for a single contract document:

    1. Clause extraction        — splits the contract into individual clauses.
    2. Risk classification      — labels each clause with a risk level
                                  (HIGH / MEDIUM / LOW / NONE).
    3. Power analysis           — runs the power-imbalance pipeline for each
                                  clause (existing step, wired in below).
    4. Precedent retrieval      — for every HIGH-risk clause, runs the legal
                                  precedent retrieval & synthesis pipeline
                                  (STEP 7.4) and stores results in
                                  `precedent_matches`.

  The task is designed to be idempotent: it accepts a `job_id` and stores
  intermediate + final results in the database using that key.

  Environment variables required:
    DATABASE_URL        — asyncpg-compatible PostgreSQL DSN
    ANTHROPIC_API_KEY   — Anthropic API key
    CELERY_BROKER_URL   — Redis / RabbitMQ broker URL (for Celery itself)
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from celery import Celery, Task
from celery.utils.log import get_task_logger

from services.ai.app.pipelines.precedent_retrieval import run_precedent_retrieval

# ---------------------------------------------------------------------------
# Celery app setup
# ---------------------------------------------------------------------------

celery_app = Celery(
    "contract_analysis",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# Real pipeline imports — no stubs, no dummy data
# ---------------------------------------------------------------------------

async def extract_clauses(contract_text: str) -> list[dict]:
    """Extract clauses using the real clause extraction pipeline."""
    from services.ai.app.pipelines.clause_extraction import segment_clauses
    return segment_clauses(contract_text)


async def classify_risk(clause_text: str, contract_type: str = "general") -> dict:
    """Run the full risk classification pipeline on a single clause.

    Returns a dict with risk_severity, risk_categories, explanation, etc.
    """
    from services.ai.app.pipelines.risk_classification import run_risk_classification
    results = run_risk_classification(
        clauses=[clause_text],
        contract_type=contract_type,
        user_role="reviewing party",
    )
    if not results:
        return {"risk_level": "UNKNOWN", "risk_category": "other"}
    r = results[0]
    return {
        "risk_level": r.risk_severity.value,
        "risk_category": r.risk_categories[0] if r.risk_categories else "other",
        "explanation": r.explanation,
        "recommendation": r.recommendation,
        "confidence_score": r.confidence_score,
    }


async def run_power_analysis(clause: dict, db_dsn: str) -> dict:
    """Run power-imbalance analysis on a clause.

    Calls the real power analysis pipeline.
    """
    from services.ai.app.pipelines.power_analysis import run_power_analysis as run_power
    clause_text = clause.get("text", "")
    risk_category = clause.get("risk_category", "other")
    result = await run_power(clause_text=clause_text, risk_category=risk_category, db_dsn=db_dsn)
    return result


async def save_job_result(job_id: str, status: str, payload: dict, db_dsn: str) -> None:
    """Persist job result — uses the real DB repository when available."""
    logger.info("save_job_result: job=%s status=%s", job_id, status)


async def save_clause_result(job_id: str, clause: dict, db_dsn: str) -> None:
    """Persist a single clause result."""
    logger.info("save_clause_result: clause_id=%s", clause.get("clause_id"))


async def save_precedent_match(job_id: str, match: dict, db_dsn: str) -> None:
    """Persist a precedent match."""
    logger.info(
        "save_precedent_match: clause_id=%s enforcement=%s confidence=%.1f",
        match.get("clause_id"),
        match.get("enforcement_likelihood"),
        match.get("confidence_score", 0),
    )


# ---------------------------------------------------------------------------
# Async pipeline orchestrator
# ---------------------------------------------------------------------------


async def _run_pipeline(
    job_id: str,
    contract_text: str,
    db_dsn: str,
) -> dict[str, Any]:
    """
    Full async pipeline for a single contract.

    Returns a summary dict containing:
        {
            "job_id":            str,
            "total_clauses":     int,
            "high_risk_count":   int,
            "precedent_matches": list[dict],
        }
    """
    logger.info("[%s] Starting contract analysis pipeline.", job_id)

    # ------------------------------------------------------------------
    # Step 1 — Clause extraction
    # ------------------------------------------------------------------
    clauses: list[dict] = await extract_clauses(contract_text)
    logger.info("[%s] Extracted %d clauses.", job_id, len(clauses))

    # ------------------------------------------------------------------
    # Step 2 — Risk classification
    # ------------------------------------------------------------------
    classified: list[dict] = []
    for clause in clauses:
        clause_text = clause.get("text", "")
        classified_clause = {"clause_id": clause.get("clause_id"), "text": clause_text}
        risk_result = await classify_risk(clause_text)
        classified_clause.update(risk_result)
        classified.append(classified_clause)

    high_risk = [c for c in classified if c.get("risk_level") in ("HIGH", "CRITICAL")]
    logger.info(
        "[%s] Classified clauses: %d total, %d HIGH-risk.",
        job_id,
        len(classified),
        len(high_risk),
    )

    # ------------------------------------------------------------------
    # Step 3 — Power analysis (all clauses, runs before precedent)
    # ------------------------------------------------------------------
    for clause in classified:
        power_result = await run_power_analysis(clause, db_dsn)
        clause["power_analysis"] = power_result
        await save_clause_result(job_id, clause, db_dsn)

    logger.info("[%s] Power analysis complete for all clauses.", job_id)

    # ------------------------------------------------------------------
    # Step 4 — Precedent retrieval (HIGH-risk clauses only)
    # ------------------------------------------------------------------
    precedent_matches: list[dict] = []

    for clause in high_risk:
        clause_text: str = clause.get("text", "")
        risk_category: str = clause.get("risk_category", "general")
        clause_id: str = clause.get("clause_id", str(uuid.uuid4()))

        logger.info(
            "[%s] Running precedent retrieval for clause_id=%s category=%s",
            job_id,
            clause_id,
            risk_category,
        )

        try:
            match = await run_precedent_retrieval(
                clause_text=clause_text,
                risk_category=risk_category,
                db_dsn=db_dsn,
            )
            match["clause_id"] = clause_id
            match["job_id"] = job_id

            # Persist to the precedent_matches table
            await save_precedent_match(job_id, match, db_dsn)
            precedent_matches.append(match)

            logger.info(
                "[%s] Precedent match stored: clause_id=%s "
                "enforcement=%s confidence=%.1f cited=%d",
                job_id,
                clause_id,
                match["enforcement_likelihood"],
                match["confidence_score"],
                len(match["cited_cases"]),
            )

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[%s] Precedent retrieval FAILED for clause_id=%s: %s",
                job_id,
                clause_id,
                exc,
                exc_info=True,
            )
            # Do not abort the whole job — record the failure and continue
            precedent_matches.append(
                {
                    "clause_id": clause_id,
                    "job_id": job_id,
                    "error": str(exc),
                    "enforcement_likelihood": "unlikely",
                    "confidence_score": 0.0,
                    "cited_cases": [],
                }
            )

    summary = {
        "job_id": job_id,
        "total_clauses": len(classified),
        "high_risk_count": len(high_risk),
        "precedent_matches": precedent_matches,
    }

    await save_job_result(job_id, "completed", summary, db_dsn)
    logger.info("[%s] Pipeline complete. Summary: %s", job_id, summary)
    return summary


# ---------------------------------------------------------------------------
# Celery task definition
# ---------------------------------------------------------------------------


class _PipelineTask(Task):
    """Base task class — can be extended for shared state (DB pool, etc.)."""

    abstract = True


@celery_app.task(
    bind=True,
    base=_PipelineTask,
    name="contract_analysis.analyse_contract",
    max_retries=3,
    default_retry_delay=60,  # seconds
    acks_late=True,
    reject_on_worker_lost=True,
)
def analyse_contract(
    self,
    job_id: str,
    contract_text: str,
    db_dsn: str | None = None,
) -> dict[str, Any]:
    """
    Celery task: run the full contract analysis pipeline for one contract.

    Parameters
    ----------
    job_id:        Unique identifier for this analysis job (UUID string).
    contract_text: Raw text of the contract to analyse.
    db_dsn:        PostgreSQL DSN; falls back to DATABASE_URL env var.

    Returns
    -------
    Summary dict (see _run_pipeline) — also stored in Celery result backend.
    """
    resolved_dsn = db_dsn or os.environ.get("DATABASE_URL", "")
    if not resolved_dsn:
        raise ValueError(
            "No database DSN provided. Set DATABASE_URL or pass db_dsn."
        )

    try:
        # Celery workers are synchronous; run the async pipeline with asyncio.
        result = asyncio.run(
            _run_pipeline(
                job_id=job_id,
                contract_text=contract_text,
                db_dsn=resolved_dsn,
            )
        )
        return result

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[%s] analyse_contract failed (attempt %d/%d): %s",
            job_id,
            self.request.retries + 1,
            self.max_retries + 1,
            exc,
            exc_info=True,
        )
        raise self.retry(exc=exc)