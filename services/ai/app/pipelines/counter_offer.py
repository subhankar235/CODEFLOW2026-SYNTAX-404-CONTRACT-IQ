"""
services/ai/pipelines/counter_offer.py
========================================
Counter-offer generation pipeline (Feature 6).

This pipeline is NOT part of the main contract scan. It runs on-demand
when the user clicks "Generate Counter-Offer", triggered by the
`generate_counter_offer` Celery task.

Flow:
  1. Embed the HIGH-risk clause
  2. Retrieve the top-1 similar favorable clause variant from pgvector
     (filtered by embedding_type="favorable_clause" AND clause_type)
  3. Load the counter_offer.txt prompt template
  4. Call PRIMARY_MODEL (claude-sonnet) with injected context
  5. Parse JSON response into CounterOfferResult Pydantic model
  6. Persist CounterOffer record to DB
  7. Return CounterOfferRecord
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.api.app.models.counter_offer import CounterOffer
from services.api.app.models.embedding import Embedding
from services.api.app.db.session import engine
from services.ai.app.pipelines.precedent_retrieval import _get_embedding_model
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from services.ai.schemas.counter_offer import (
    CounterOfferRequest,
    CounterOfferResult,
    CounterOfferRecord,
    CounterOfferVersion
)

log = logging.getLogger(__name__)

# Sync session for pgvector queries
_sync_engine = create_engine(os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql"))
SyncSession = sessionmaker(bind=_sync_engine)


def get_sync_session():
    return SyncSession()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "claude-opus-4-6")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
COUNTER_OFFER_PROMPT_PATH = PROMPTS_DIR / "counter_offer.txt"

MAX_TOKENS = 2048
TOP_K_RETRIEVAL = 1  # Retrieve top-1 favorable variant


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_favorable_clause(
    session: Session,
    clause_embedding: list[float],
    clause_type: str,
    top_k: int = TOP_K_RETRIEVAL,
) -> Optional[Embedding]:
    """
    Retrieve the most similar favorable clause variant from pgvector.
    Filters by embedding_type='favorable_clause' and clause_type.

    Uses cosine distance (<=> operator) for similarity search.
    """
    # Use raw SQL for pgvector cosine distance operator
    vector_str = "[" + ",".join(str(v) for v in clause_embedding) + "]"

    result = session.execute(
        text(
            """
            SELECT id, text AS content, context_data->>'clause_type' AS clause_type, context_data
            FROM embeddings
            WHERE embedding_type = 'favorable_clause'
              AND context_data->>'clause_type' = :clause_type
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
            """
        ),
        {
            "clause_type": clause_type,
            "embedding": vector_str,
            "top_k": top_k,
        },
    ).fetchall()

    if not result:
        log.warning(
            "No favorable clause variants found for clause_type=%s — "
            "trying without clause_type filter",
            clause_type,
        )
        # Fallback: search across all favorable clauses
        result = session.execute(
            text(
                """
                SELECT id, text AS content, context_data->>'clause_type' AS clause_type, context_data
                FROM embeddings
                WHERE embedding_type = 'favorable_clause'
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {"embedding": vector_str, "top_k": top_k},
        ).fetchall()

    if not result:
        return None

    row = result[0]
    # Reconstruct a lightweight Embedding-like object from the row
    emb = Embedding()
    emb.id = row.id
    emb.content = row.content
    emb.clause_type = row.clause_type
    emb.source_id = None
    emb.metadata_ = row.context_data
    return emb


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

from ..prompts.prompt_loader import load_prompt


def _build_prompt(
    original_clause: str,
    favorable_reference: str,
    contract_type: str,
    user_role: str,
    risk_category: str,
) -> tuple[str, str]:
    values = {
        "original_clause": original_clause,
        "favorable_reference": favorable_reference,
        "contract_type": contract_type,
        "user_role": user_role,
        "risk_category": risk_category,
    }
    return load_prompt("counter_offer", values)


async def _call_llm_async(system_prompt: str, user_prompt: str) -> str:
    from services.ai.app.models.openrouter_client import OpenRouterClient
    client = OpenRouterClient()
    raw_response = await client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=PRIMARY_MODEL,
        json_mode=False,
    )
    content = raw_response["choices"][0]["message"].get("content", "")
    return content


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the PRIMARY_MODEL via the OpenRouter API.
    Returns the raw text content of the response.
    """
    import asyncio
    import concurrent.futures

    try:
        asyncio.get_running_loop()
        has_loop = True
    except RuntimeError:
        has_loop = False

    if has_loop:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                _call_llm_async(system_prompt, user_prompt),
            )
            return future.result()
    else:
        return asyncio.run(_call_llm_async(system_prompt, user_prompt))


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> CounterOfferResult:
    """Parse the LLM JSON response into a CounterOfferResult."""
    # Strip accidental markdown fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # Remove first and last fence lines
        inner = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(inner).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw response:\n{raw}") from e

    def _parse_version(key: str) -> CounterOfferVersion:
        v = data.get(key)
        if not v:
            raise ValueError(f"Missing '{key}' key in LLM response")
        return CounterOfferVersion(
            clause=v["clause"],
            explanation=v["explanation"],
        )

    result = CounterOfferResult(
        aggressive=_parse_version("aggressive"),
        balanced=_parse_version("balanced"),
        conservative=_parse_version("conservative"),
        negotiation_email=data["negotiation_email"],
    )

    # Verify all three clauses differ from each other
    clauses = {
        result.aggressive.clause.strip(),
        result.balanced.clause.strip(),
        result.conservative.clause.strip(),
    }
    if len(clauses) < 3:
        raise ValueError(
            "Counter-offer versions must be substantively different from each other"
        )

    return result


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _persist_counter_offer(
    session: Session,
    request: CounterOfferRequest,
    result: CounterOfferResult,
    favorable_ref_id: Optional[uuid.UUID],
    raw_response: str,
) -> CounterOffer:
    record = CounterOffer(
        id=uuid.uuid4(),
        clause_id=request.clause_id,
        aggressive_version=result.aggressive.clause,
        balanced_version=result.balanced.clause,
        conservative_version=result.conservative.clause,
        negotiation_email=result.negotiation_email,
    )
    session.add(record)
    session.flush()  # Assigns DB-generated fields without full commit
    return record


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_counter_offer(request: CounterOfferRequest) -> CounterOfferRecord:
    """
    Main pipeline entry point.

    Steps:
      1. Embed the clause text
      2. Retrieve most similar favorable variant from pgvector
      3. Build prompt and call LLM
      4. Parse response into Pydantic model
      5. Persist to counter_offers table
      6. Return CounterOfferRecord

    Raises:
      EnvironmentError: Missing API key
      httpx.HTTPStatusError: API call failure
      ValueError: LLM response parsing failure
    """
    log.info(
        "Generating counter-offer for clause_id=%s, risk_category=%s",
        request.clause_id,
        request.risk_category,
    )

    # Step 1: Embed the clause
    log.debug("Embedding clause text (%d chars)…", len(request.clause_text))
    clause_embedding = _get_embedding_model().encode(request.clause_text).tolist()

    # Steps 2–6 in a single DB session
    with get_sync_session() as session:
        # Step 2: Retrieve favorable reference
        favorable_ref = retrieve_favorable_clause(
            session=session,
            clause_embedding=clause_embedding,
            clause_type=request.risk_category,
        )

        if favorable_ref:
            log.info(
                "Favorable reference retrieved: clause_type=%s, source=%s",
                favorable_ref.clause_type,
                favorable_ref.source_id,
            )
            favorable_text = favorable_ref.content
            favorable_ref_id = favorable_ref.id
        else:
            log.warning("No favorable reference found — proceeding without retrieval context")
            favorable_text = (
                "No specific reference clause available. "
                "Apply best-practice protective language for this clause type."
            )
            favorable_ref_id = None

        # Step 3: Build and send prompt
        system_prompt, user_prompt = _build_prompt(
            original_clause=request.clause_text,
            favorable_reference=favorable_text,
            contract_type=request.contract_type,
            user_role=request.user_role,
            risk_category=request.risk_category,
        )
        log.debug("Calling PRIMARY_MODEL=%s…", PRIMARY_MODEL)
        raw_response = _call_llm(system_prompt, user_prompt)
        log.debug("LLM response received (%d chars)", len(raw_response))

        # Step 4: Parse
        result = _parse_response(raw_response)
        log.info("Counter-offer parsed successfully (3 versions + email)")

        # Step 5: Persist
        db_record = _persist_counter_offer(
            session=session,
            request=request,
            result=result,
            favorable_ref_id=favorable_ref_id,
            raw_response=raw_response,
        )

        created_at = db_record.created_at or datetime.now(timezone.utc)
        record_id = db_record.id

    log.info("Counter-offer stored: id=%s", record_id)

    # Step 6: Return
    return CounterOfferRecord(
        id=record_id,
        clause_id=request.clause_id,
        result=result,
        favorable_reference_id=favorable_ref_id,
        created_at=created_at,
    )