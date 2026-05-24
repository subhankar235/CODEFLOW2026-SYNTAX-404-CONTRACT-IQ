"""
Celery task for translating results to a different language (STEP 9.2).
Triggered on-demand when user switches language post-scan.
"""

import asyncio
import logging
from uuid import UUID
from typing import Dict, Any, List

from celery import Task
from celery.utils.log import get_task_logger

from apps.worker.celery_app import celery_app as app
from services.api.app.db.session import SessionLocal

logger = get_task_logger(__name__)


def _get_contract_data(contract_id: UUID) -> Dict[str, Any] | None:
    """Fetch contract and all results from DB (sync wrapper for Celery)."""
    return asyncio.run(_fetch_contract_data(contract_id))


async def _fetch_contract_data(contract_id: UUID) -> Dict[str, Any] | None:
    """Async function to fetch contract, clauses, and analysis results."""
    async with SessionLocal() as db:
        from sqlalchemy import select, func
        from services.api.app.models.contract import Contract
        from services.api.app.models.analysis_result import AnalysisResult

        # Get contract
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalars().first()

        if not contract:
            return None

        # Get all clauses
        from services.api.app.models.clause import Clause

        clauses_result = await db.execute(
            select(Clause)
            .where(Clause.contract_id == contract_id)
            .order_by(Clause.position_index)
        )
        clauses = clauses_result.scalars().all()

        # Get analysis result
        analysis_result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.contract_id == contract_id)
        )
        analysis = analysis_result.scalars().first()

        return {
            "contract_id": str(contract.id),
            "detected_language": contract.detected_language or "en",
            "clauses": [
                {
                    "id": str(c.id),
                    "text": c.text,
                    "plain_english": c.plain_english,
                    "worst_case_scenario": c.worst_case_scenario,
                    "headline": c.headline,
                    "scenario": c.scenario,
                }
                for c in clauses
            ],
            "analysis": {
                "one_liner": analysis.one_liner if analysis else None,
                "top_concerns": analysis.top_concerns if analysis else [],
                "top_positives": analysis.top_positives if analysis else [],
            }
            if analysis
            else None,
        }


def _update_translated_results(
    contract_id: UUID,
    translated_data: Dict[str, Any],
) -> None:
    """Update DB with translated results (sync wrapper for Celery)."""
    asyncio.run(_save_translated_results(contract_id, translated_data))


async def _save_translated_results(
    contract_id: UUID,
    translated_data: Dict[str, Any],
) -> None:
    """Async function to update clauses and analysis with translated text."""
    async with SessionLocal() as db:
        from sqlalchemy import select
        from services.api.app.models.clause import Clause
        from services.api.app.models.analysis_result import AnalysisResult

        # Update clauses
        for clause_data in translated_data.get("clauses", []):
            result = await db.execute(
                select(Clause).where(Clause.id == UUID(clause_data["id"]))
            )
            clause = result.scalars().first()
            if clause:
                if "plain_english" in clause_data:
                    clause.plain_english = clause_data["plain_english"]
                if "worst_case_scenario" in clause_data:
                    clause.worst_case_scenario = clause_data["worst_case_scenario"]
                if "headline" in clause_data:
                    clause.headline = clause_data["headline"]
                if "scenario" in clause_data:
                    clause.scenario = clause_data["scenario"]

        # Update analysis result
        analysis_data = translated_data.get("analysis")
        if analysis_data:
            result = await db.execute(
                select(AnalysisResult).where(AnalysisResult.contract_id == contract_id)
            )
            analysis = result.scalars().first()
            if analysis:
                if "one_liner" in analysis_data:
                    analysis.one_liner = analysis_data["one_liner"]
                if "top_concerns" in analysis_data:
                    analysis.top_concerns = analysis_data["top_concerns"]
                if "top_positives" in analysis_data:
                    analysis.top_positives = analysis_data["top_positives"]

        await db.commit()
        logger.info("Translated results saved for contract %s", contract_id)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def translate_results_task(
    self, contract_id_str: str, target_language: str
) -> Dict[str, Any]:
    """
    Celery task to translate contract results to a different language.

    Parameters
    ----------
    contract_id_str : str
        UUID of the contract.
    target_language : str
        Target language code (e.g., "es", "fr").

    Returns
    -------
    dict
        Status summary.
    """
    contract_id = UUID(contract_id_str)
    logger.info(
        "Starting translation to %s for contract %s", target_language, contract_id
    )

    try:
        # Fetch contract data
        contract_data = _get_contract_data(contract_id)
        if not contract_data:
            raise ValueError(f"Contract {contract_id} not found")

        if target_language == contract_data["detected_language"]:
            logger.info("Contract already in %s, skipping translation", target_language)
            return {"status": "skipped", "reason": "already in target language"}

        logger.info("Translating results to %s", target_language)

        # Translate all texts in batch
        from app.multilingual.translator import translate_batch

        # Collect all texts to translate
        texts_to_translate = []
        text_references = []  # Track which field each text belongs to

        for clause in contract_data["clauses"]:
            for field in [
                "plain_english",
                "worst_case_scenario",
                "headline",
                "scenario",
            ]:
                if clause.get(field):
                    texts_to_translate.append(clause[field])
                    text_references.append(("clause", clause["id"], field))

        if contract_data.get("analysis"):
            analysis = contract_data["analysis"]
            for field in ["one_liner"]:
                if analysis.get(field):
                    texts_to_translate.append(analysis[field])
                    text_references.append(("analysis", None, field))
            for field in ["top_concerns", "top_positives"]:
                if analysis.get(field):
                    for i, item in enumerate(analysis[field]):
                        texts_to_translate.append(item)
                        text_references.append(("analysis_list", field, i))

        if not texts_to_translate:
            logger.info("No texts to translate")
            return {"status": "completed", "translated": 0}

        # Perform batch translation
        translated_texts = translate_batch(
            texts_to_translate,
            source_lang="en",
            target_lang=target_language,
        )

        # Map translated texts back to their fields
        translated_clauses = {}
        translated_analysis = {}

        for t, ref in zip(translated_texts, text_references):
            if ref[0] == "clause":
                clause_id = ref[1]
                field = ref[2]
                if clause_id not in translated_clauses:
                    translated_clauses[clause_id] = {}
                translated_clauses[clause_id][field] = t
            elif ref[0] == "analysis":
                field = ref[2]
                if "analysis" not in translated_analysis:
                    translated_analysis["analysis"] = {}
                translated_analysis["analysis"][field] = t
            elif ref[0] == "analysis_list":
                field = ref[1]
                index = ref[2]
                if "analysis" not in translated_analysis:
                    translated_analysis["analysis"] = {}
                if field not in translated_analysis["analysis"]:
                    translated_analysis["analysis"][field] = []
                translated_analysis["analysis"][field].append(t)

        # Prepare data for DB update
        update_data = {
            "clauses": [
                {"id": c["id"], **translated_clauses.get(c["id"], {})}
                for c in contract_data["clauses"]
            ],
            "analysis": translated_analysis.get("analysis"),
        }

        # Save to DB
        _update_translated_results(contract_id, update_data)

        logger.info(
            "Translation to %s complete: %d texts translated",
            target_language,
            len(texts_to_translate),
        )
        return {
            "status": "completed",
            "contract_id": str(contract_id),
            "target_language": target_language,
            "translated": len(texts_to_translate),
        }

    except Exception as exc:
        logger.error("Translation failed for contract %s: %s", contract_id, exc)

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
            logger.error("Max retries exceeded for contract %s", contract_id)
            raise
