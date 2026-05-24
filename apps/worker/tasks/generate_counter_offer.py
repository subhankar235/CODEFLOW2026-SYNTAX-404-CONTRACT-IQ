"""
Celery task for counter-offer generation (STEP 7.6).
Triggered on-demand when user requests a counter-offer for a HIGH-risk clause.
"""

import asyncio
import logging
from uuid import UUID
from typing import Dict, Any

from celery import Task
from celery.utils.log import get_task_logger

from apps.worker.celery_app import celery_app as app
from services.api.app.db.session import SessionLocal

logger = get_task_logger(__name__)


def _get_clause_data(clause_id: UUID) -> Dict[str, Any] | None:
    """Fetch clause and contract data from DB (sync wrapper for Celery)."""
    return asyncio.run(_fetch_clause_data(clause_id))


async def _fetch_clause_data(clause_id: UUID) -> Dict[str, Any] | None:
    """Async function to fetch clause and related contract data."""
    async with SessionLocal() as db:
        from services.api.app.repositories.clause_repo import get_clause_by_id

        clause = await get_clause_by_id(db, clause_id)
        if not clause:
            return None

        # Get contract for contract_type
        from services.api.app.models.contract import Contract
        from sqlalchemy import select

        result = await db.execute(
            select(Contract).where(Contract.id == clause.contract_id)
        )
        contract = result.scalars().first()

        return {
            "clause_id": str(clause.id),
            "clause_text": clause.text,
            "risk_category": clause.risk_category or "other",
            "contract_type": (contract.contract_type if contract else None) or "Unknown",
            "user_role": "Client",
        }


def _store_counter_offer(clause_id: UUID, result: Dict[str, Any]) -> None:
    """Store the counter-offer result in DB (sync wrapper for Celery)."""
    asyncio.run(_save_counter_offer(clause_id, result))


async def _save_counter_offer(clause_id: UUID, result: Dict[str, Any]) -> None:
    """Async function to save counter-offer to database."""
    async with SessionLocal() as db:
        # Check if already exists
        from sqlalchemy import select
        from services.api.app.models.counter_offer import CounterOffer

        existing = await db.execute(
            select(CounterOffer).where(CounterOffer.clause_id == clause_id)
        )
        if existing.scalars().first():
            logger.info("Counter-offer already exists for clause %s", clause_id)
            return

        counter_offer = CounterOffer(
            clause_id=clause_id,
            aggressive_version=result.get("aggressive", ""),
            balanced_version=result.get("balanced", ""),
            conservative_version=result.get("conservative", ""),
            negotiation_email=result.get("negotiation_email", ""),
        )
        db.add(counter_offer)
        await db.commit()
        logger.info("Counter-offer stored for clause %s", clause_id)


@app.task(name="generate_counter_offer", bind=True, max_retries=3, default_retry_delay=60)
def generate_counter_offer_task(self, clause_id_str: str) -> Dict[str, Any]:
    """
    Celery task to generate a counter-offer for a HIGH-risk clause.

    Parameters
    ----------
    clause_id_str : str
        UUID of the Clause to generate counter-offer for.

    Returns
    -------
    dict
        Counter-offer result with aggressive, balanced, conservative versions.
    """
    clause_id = UUID(clause_id_str)
    logger.info("Starting counter-offer generation for clause %s", clause_id)

    try:
        # Fetch clause data
        clause_data = _get_clause_data(clause_id)
        if not clause_data:
            raise ValueError(f"Clause {clause_id} not found")

        logger.info(
            "Generating counter-offer for clause with risk: %s",
            clause_data["risk_category"],
        )

        # Call the AI pipeline
        from services.ai.app.pipelines.counter_offer import (
            generate_counter_offer as ai_generate,
        )

        # Build request object expected by the pipeline
        from services.ai.schemas.counter_offer import CounterOfferRequest

        request = CounterOfferRequest(
            clause_id=clause_data["clause_id"],
            clause_text=clause_data["clause_text"],
            risk_category=clause_data["risk_category"],
            contract_type=clause_data["contract_type"],
            user_role=clause_data["user_role"],
        )

        # Run the pipeline
        result_obj = ai_generate(request)

        # Convert result to dict
        result = {
            "aggressive": result_obj.result.aggressive.clause
            if result_obj.result
            else "",
            "balanced": result_obj.result.balanced.clause if result_obj.result else "",
            "conservative": result_obj.result.conservative.clause
            if result_obj.result
            else "",
            "negotiation_email": result_obj.result.negotiation_email
            if result_obj.result
            else "",
        }

        # Store in DB
        _store_counter_offer(clause_id, result)

        logger.info("Counter-offer generation complete for clause %s", clause_id)
        return result

    except Exception as exc:
        logger.error(
            "Counter-offer generation failed for clause %s: %s", clause_id, exc
        )

        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2**self.request.retries)
            logger.warning(
                "Retrying in %d seconds (attempt %d/%d)",
                retry_delay,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error("Max retries exceeded for clause %s", clause_id)
            raise
