"""
Celery task for contract embedding (STEP 8.1).
Embeds contract text chunks and stores them in pgvector for Q&A RAG.
"""

import asyncio
import logging
from uuid import UUID
from typing import List, Dict, Any

from celery import Task
from celery.utils.log import get_task_logger

from apps.worker.celery_app import celery_app as app
from services.api.app.db.session import SessionLocal

logger = get_task_logger(__name__)


def _get_contract_text(contract_id: UUID) -> str | None:
    """Fetch contract text from DB (sync wrapper for Celery)."""
    return asyncio.run(_fetch_contract_text(contract_id))


async def _fetch_contract_text(contract_id: UUID) -> str | None:
    """Async function to fetch contract and its clauses."""
    async with SessionLocal() as db:
        from sqlalchemy import select
        from services.api.app.models.contract import Contract

        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalars().first()

        if not contract:
            return None

        # Get all clauses for this contract
        from services.api.app.models.clause import Clause

        clauses_result = await db.execute(
            select(Clause)
            .where(Clause.contract_id == contract_id)
            .order_by(Clause.position_index)
        )
        clauses = clauses_result.scalars().all()

        # Combine all clause texts
        return "\n\n".join(c.text for c in clauses if c.text)


def _store_embeddings(contract_id: UUID, chunks_data: List[Dict[str, Any]]) -> None:
    """Store embeddings in pgvector (sync wrapper for Celery)."""
    asyncio.run(_save_embeddings(contract_id, chunks_data))


async def _save_embeddings(
    contract_id: UUID, chunks_data: List[Dict[str, Any]]
) -> None:
    """Async function to store embeddings in DB."""
    async with SessionLocal() as db:
        from services.api.app.models.embedding import Embedding

        # Check if embeddings already exist
        from sqlalchemy import select, func

        existing = await db.execute(
            select(func.count(Embedding.id)).where(
                (Embedding.contract_id == contract_id)
                & (Embedding.embedding_type == "contract_qa")
            )
        )
        if existing.scalar_one() > 0:
            logger.info("Embeddings already exist for contract %s", contract_id)
            return

        # Create embedding records
        for chunk in chunks_data:
            embedding = Embedding(
                contract_id=contract_id,
                text=chunk["chunk_text"],
                embedding_type="contract_qa",
                embedding=chunk["embedding_vector"],
                context_data={"chunk_index": chunk["chunk_index"]},
            )
            db.add(embedding)

        await db.commit()
        logger.info(
            "Stored %d embeddings for contract %s", len(chunks_data), contract_id
        )


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def embed_contract_task(self, contract_id_str: str) -> Dict[str, Any]:
    """
    Celery task to embed a contract for Q&A RAG.

    Parameters
    ----------
    contract_id_str : str
        UUID of the Contract to embed.

    Returns
    -------
    dict
        Status summary with chunk count.
    """
    contract_id = UUID(contract_id_str)
    logger.info("Starting contract embedding for contract %s", contract_id)

    try:
        # Fetch contract text
        contract_text = _get_contract_text(contract_id)
        if not contract_text:
            raise ValueError(f"Contract {contract_id} not found or has no text")

        logger.info("Embedding contract with %d characters", len(contract_text))

        # Chunk and embed
        from services.ai.app.utils.chunk_splitter import split_into_chunks
        from services.ai.app.rag.embedding_service import chunk_and_embed

        chunks = split_into_chunks(contract_text)
        chunks_data = chunk_and_embed(contract_text)

        # Store in pgvector
        _store_embeddings(contract_id, chunks_data)

        logger.info(
            "Contract embedding complete for %s: %d chunks",
            contract_id,
            len(chunks_data),
        )
        return {
            "status": "completed",
            "contract_id": str(contract_id),
            "chunks_count": len(chunks_data),
        }

    except ModuleNotFoundError as exc:
        # A missing dependency (e.g. sentence_transformers) is a permanent
        # configuration problem — retrying will never fix it, so fail fast.
        logger.error(
            "Embedding dependency missing for contract %s — "
            "install required packages: %s",
            contract_id,
            exc,
        )
        raise
    except Exception as exc:
        logger.error("Contract embedding failed for %s: %s", contract_id, exc)

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
