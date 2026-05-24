"""
STEP 7.4 — Legal Precedent Retrieval Pipeline
-----------------------------------------------
PURPOSE:
  This pipeline answers the question: "Has this type of clause been
  tested in court — and what happened?"

  It uses Retrieval-Augmented Generation (RAG) to:
    1. Embed the clause text into a vector using a sentence-transformer model
    2. Search a pgvector database of pre-indexed legal precedent summaries
       to find the 3 most similar cases (filtered by risk category)
    3. Feed those retrieved cases into the AI model as grounding context
    4. Parse the AI's synthesis into a structured PrecedentMatch result

  The confidence score blends pgvector similarity (how relevant the
  retrieved cases are) with the model's own self-rated confidence.

  Only HIGH-risk clauses go through this pipeline — it's expensive
  (embedding + vector search + AI call per clause).

FLOW:
  [HIGH clause] → embed → pgvector search (top 3) → AI synthesis
  → parse PrecedentMatch → calculate confidence → store → return

HOW IT FITS IN:
  Called from the main Celery task AFTER power analysis completes.
  Runs once per HIGH-risk clause (in sequence or parallel).
  Results stored in the precedent_matches table.

PREREQUISITES:
  - pgvector extension enabled in PostgreSQL
  - embeddings table pre-seeded with legal precedent summaries
    (see STEP 7.5 for seeding script)
  - sentence-transformers package installed
  - DATABASE_URL environment variable set
"""

import os
import json
import logging
from typing import List, Optional

import anthropic
from pydantic import BaseModel, field_validator
from sentence_transformers import SentenceTransformer
import psycopg2
import psycopg2.extras

from services.ai.app.utils.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

# Embedding model — all-MiniLM-L6-v2 is fast, small (80 MB), and accurate
# enough for legal clause similarity (384-dimensional embeddings)
_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model: Optional[SentenceTransformer] = None  # lazy-loaded singleton


def _get_embedding_model() -> SentenceTransformer:
    """
    Lazy-loads the sentence-transformer model.
    We load it once and reuse it across pipeline calls to save memory.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", _EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
    return _embedding_model


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class HighRiskClause(BaseModel):
    """Input: a single HIGH-risk clause to run precedent retrieval for."""
    clause_id:     str
    clause_type:   str   # e.g. "non-compete", "indemnity", "ip_assignment"
    clause_text:   str
    risk_category: str   # Used to filter the pgvector search


class CitedCase(BaseModel):
    """A single legal case cited in the precedent synthesis."""
    name:         str   # e.g. "Solari Industries, Inc. v. Malady"
    year:         int | None = None  # e.g. 1970
    jurisdiction: str | None = None  # e.g. "California Supreme Court"
    outcome:      str   # Brief plain-language outcome description


class RetrievedPrecedent(BaseModel):
    """
    A single precedent case retrieved from the pgvector embeddings table.
    This is an internal model — not returned to callers.
    """
    case_name:    str
    summary:      str
    similarity:   float   # Cosine similarity score from pgvector (0.0–1.0)
    risk_category: str


class PrecedentMatch(BaseModel):
    """
    The final output for a single HIGH-risk clause.
    Stored in the precedent_matches table.
    """
    clause_id:              str
    precedent_summary:      str    # AI-synthesised summary of relevant precedents
    enforcement_likelihood: str    # One of four defined values (see validator)
    confidence_score:       int    # 0–100, blended retrieval × LLM confidence
    cited_cases:            List[CitedCase]  # 1–3 items

    @field_validator("enforcement_likelihood")
    @classmethod
    def validate_enforcement(cls, v: str) -> str:
        # The four allowed enforcement likelihood values
        allowed = {
            "Very Likely Enforced",
            "Likely Enforced",
            "Unlikely Enforced",
            "Rarely Enforced",
        }
        if v not in allowed:
            raise ValueError(
                f"enforcement_likelihood must be one of {allowed}, got '{v}'"
            )
        return v

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError(f"confidence_score must be 0–100, got {v}")
        return v

    @field_validator("cited_cases")
    @classmethod
    def validate_cited_cases(cls, v: List[CitedCase]) -> List[CitedCase]:
        if not (1 <= len(v) <= 3):
            raise ValueError(
                f"cited_cases must have 1–3 items, got {len(v)}"
            )
        return v


# ---------------------------------------------------------------------------
# Step 1: Embed clause text
# ---------------------------------------------------------------------------

def _embed_clause(clause_text: str) -> List[float]:
    """
    Converts the clause text into a 384-dimensional vector.
    Used to query the pgvector index for similar precedent cases.
    """
    model     = _get_embedding_model()
    embedding = model.encode(clause_text, convert_to_numpy=True)
    return embedding.tolist()


# ---------------------------------------------------------------------------
# Step 2: pgvector similarity search
# ---------------------------------------------------------------------------

def _retrieve_similar_precedents(
    embedding:     List[float],
    risk_category: str,
    top_k:         int = 3,
) -> List[RetrievedPrecedent]:
    """
    Performs a cosine similarity search against the embeddings table
    to find the top-k precedent cases most similar to the clause.

    Filters by risk_category so a "Financial" clause doesn't accidentally
    retrieve IP or Privacy precedents.

    Expected table schema:
        embeddings (
            id             UUID PRIMARY KEY,
            case_name      TEXT,
            summary        TEXT,
            risk_category  TEXT,
            embedding_type TEXT,   -- must be 'precedent' for this pipeline
            embedding      VECTOR(384)
        )

    pgvector operator <=> = cosine distance (lower = more similar)
    We convert to similarity = 1 - distance for readability.
    """
    conn_str = os.environ["DATABASE_URL"]

    # Format the embedding as a pgvector literal string
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    query = """
        SELECT
            context_data->>'case_name' AS case_name,
            context_data->>'summary' AS summary,
            context_data->>'clause_type' AS risk_category,
            1 - (embedding <=> %s::vector) AS similarity
        FROM embeddings
        WHERE embedding_type = 'precedent'
          AND context_data->>'clause_type' = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """

    with psycopg2.connect(conn_str) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (embedding_str, risk_category, embedding_str, top_k))
            rows = cur.fetchall()

    if not rows:
        logger.warning(
            "No precedents found for risk_category='%s'. "
            "Check that the embeddings table is seeded (STEP 7.5).",
            risk_category,
        )

    results = [
        RetrievedPrecedent(
            case_name     = row["case_name"],
            summary       = row["summary"],
            similarity    = float(row["similarity"]),
            risk_category = row["risk_category"],
        )
        for row in rows
    ]

    logger.debug(
        "Retrieved %d precedents for category='%s', similarities=%s",
        len(results), risk_category,
        [round(r.similarity, 3) for r in results],
    )
    return results


# ---------------------------------------------------------------------------
# Step 3: Build prompt and call AI model
# ---------------------------------------------------------------------------

def _build_precedent_prompt(
    clause:     HighRiskClause,
    precedents: List[RetrievedPrecedent],
) -> str:
    """
    Injects the clause text and retrieved case summaries into the
    precedent.txt prompt template.
    """
    case_block = "\n\n".join(
        f"Case {i+1}: {p.case_name}\nSimilarity: {p.similarity:.2f}\n{p.summary}"
        for i, p in enumerate(precedents)
    )

    return f"""You are a senior legal analyst specialising in contract enforcement.
A contract contains the following HIGH-risk clause:

Clause Type:   {clause.clause_type}
Risk Category: {clause.risk_category}

Clause Text:
\"\"\"{clause.clause_text}\"\"\"

Based ONLY on the retrieved legal precedents below, synthesise an analysis.

RETRIEVED PRECEDENTS:
{case_block}

Respond ONLY with valid JSON — no markdown, no explanation outside JSON.
{{
  "precedent_summary":      "<2-3 sentence synthesis of how courts have treated this clause type>",
  "enforcement_likelihood": "<exactly one of: Very Likely Enforced | Likely Enforced | Unlikely Enforced | Rarely Enforced>",
  "confidence_score":       <integer 0-100, your self-rated confidence based on precedent quality>,
  "cited_cases":            [
    {{"name": "<case name>", "year": <year as integer>, "jurisdiction": "<court name>", "outcome": "<brief plain-language outcome>"}},
    ...
  ]
}}
Include 1–3 items in cited_cases. Only cite cases from the retrieved precedents above."""


# ---------------------------------------------------------------------------
# Step 4: Store result in DB
# ---------------------------------------------------------------------------

def _store_precedent_match(clause_id: str, match: PrecedentMatch) -> None:
    """
    Persists the precedent match result to the precedent_matches table.
    """
    import uuid
    import json
    
    conn_str = os.environ["DATABASE_URL"]
    
    # cited_cases needs to be serialized to JSON
    # we convert CitedCase models into dictionaries first
    cited_cases_data = [
        {
            "name": c.name,
            "year": c.year,
            "jurisdiction": c.jurisdiction,
            "outcome": c.outcome
        }
        for c in match.cited_cases
    ]
    
    delete_query = "DELETE FROM precedent_matches WHERE clause_id = %s;"
    
    insert_query = """
        INSERT INTO precedent_matches (id, clause_id, precedent_summary, enforcement_likelihood, confidence_score, cited_cases, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW());
    """
    
    try:
        with psycopg2.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # Remove any existing match to avoid duplicate row issues (or unique constraint issues)
                cur.execute(delete_query, (uuid.UUID(clause_id),))
                
                # Insert the new match
                match_id = uuid.uuid4()
                cur.execute(
                    insert_query,
                    (
                        match_id,
                        uuid.UUID(clause_id),
                        match.precedent_summary,
                        match.enforcement_likelihood,
                        float(match.confidence_score),
                        json.dumps(cited_cases_data)
                    )
                )
        logger.info(
            "Successfully stored precedent match in database for clause_id=%s",
            clause_id
        )
    except Exception as e:
        logger.error(
            "Failed to persist precedent match to database for clause_id=%s: %s",
            clause_id, e
        )


# ---------------------------------------------------------------------------
# LLM Call Helpers
# ---------------------------------------------------------------------------

async def _call_llm_async(system_prompt: str, user_prompt: str, model: str) -> str:
    from services.ai.app.models.openrouter_client import OpenRouterClient
    client = OpenRouterClient()
    raw_response = await client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        json_mode=True,
    )
    content = raw_response.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content or ""


def _call_llm(system_prompt: str, user_prompt: str, model: str) -> str:
    """
    Call the model via OpenRouterClient.
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
                _call_llm_async(system_prompt, user_prompt, model),
            )
            return future.result()
    else:
        return asyncio.run(_call_llm_async(system_prompt, user_prompt, model))


# ---------------------------------------------------------------------------
# Core pipeline function
# ---------------------------------------------------------------------------

def run_precedent_retrieval(
    clause:        HighRiskClause,
    primary_model: str = "claude-sonnet-4-20250514",
) -> PrecedentMatch:
    """
    Main entry point for the Legal Precedent Retrieval Pipeline.

    Steps:
      1. Embed the clause text using sentence-transformers.
      2. Query pgvector for the top-3 most similar precedent cases
         (filtered by risk_category).
      3. Call the AI model with the clause + retrieved cases as context.
      4. Parse the AI response into a PrecedentMatch.
      5. Calculate the blended confidence score using the confidence_scorer.
      6. Store the result in the precedent_matches table.
      7. Return the PrecedentMatch.

    Args:
        clause:        A single HIGH-risk clause (callers should filter for HIGH only).
        primary_model: Anthropic model ID for the synthesis step.

    Returns:
        PrecedentMatch — the complete precedent analysis for this clause.
    """
    logger.info(
        "Precedent retrieval pipeline: clause_id=%s type=%s category=%s",
        clause.clause_id, clause.clause_type, clause.risk_category,
    )

    # Step 1: Embed
    embedding = _embed_clause(clause.clause_text)
    logger.debug("Clause embedded: %d dimensions", len(embedding))

    # Step 2: Retrieve similar precedents from pgvector
    precedents = _retrieve_similar_precedents(embedding, clause.risk_category, top_k=3)

    if not precedents:
        # Graceful degradation: no precedents → return low-confidence result
        logger.warning(
            "No precedents retrieved for clause_id=%s. Returning empty match.",
            clause.clause_id,
        )
        empty_match = PrecedentMatch(
            clause_id              = clause.clause_id,
            precedent_summary      = "No relevant precedents found in the corpus.",
            enforcement_likelihood = "Unlikely Enforced",
            confidence_score       = 0,
            cited_cases            = [CitedCase(
                name         = "No case found",
                year         = 0,
                jurisdiction = "N/A",
                outcome      = "No precedent data available for this clause type.",
            )],
        )
        _store_precedent_match(clause.clause_id, empty_match)
        return empty_match

    # Step 3: Call AI model for synthesis
    prompt = _build_precedent_prompt(clause, precedents)
    system_prompt = "You are a senior legal analyst specialising in contract enforcement. Respond ONLY with a valid JSON object."
    model_to_use = os.getenv("PRIMARY_MODEL", "meta-llama/llama-3.3-70b-instruct")

    try:
        raw_text = _call_llm(system_prompt=system_prompt, user_prompt=prompt, model=model_to_use).strip()

        # Step 4: Parse AI response
        raw_json = json.loads(raw_text)

        # Extract LLM's self-rated confidence BEFORE overwriting it
        # with the blended score (so calculate_confidence_score gets the raw value)
        llm_confidence = int(raw_json.get("confidence_score", 50))

        # Deserialise cited_cases
        raw_json["cited_cases"] = [
            CitedCase(**c) for c in raw_json.get("cited_cases", [])
        ]

        # Step 5: Calculate blended confidence score
        # Formula: avg(retrieval_similarities) × llm_confidence
        retrieval_similarities = [p.similarity for p in precedents]
        blended_confidence     = ConfidenceScorer.compute(
            sum(retrieval_similarities)/len(retrieval_similarities) if retrieval_similarities else 0, llm_confidence
        )

        # Overwrite the model's raw self-rating with the blended score
        raw_json["confidence_score"] = blended_confidence
        raw_json["clause_id"]        = clause.clause_id

        match = PrecedentMatch(**raw_json)

        # Step 6: Persist to DB
        _store_precedent_match(clause.clause_id, match)

        logger.info(
            "✓ Precedent match: clause_id=%s likelihood='%s' confidence=%d "
            "cited=%d sims=%s",
            clause.clause_id, match.enforcement_likelihood, match.confidence_score,
            len(match.cited_cases),
            [round(s, 2) for s in retrieval_similarities],
        )
        return match

    except json.JSONDecodeError as e:
        logger.error("JSON parse error in precedent pipeline for clause_id=%s: %s",
                     clause.clause_id, e)
        raise
    except Exception as e:
        logger.error("Precedent retrieval failed for clause_id=%s: %s",
                     clause.clause_id, e)
        raise


# ---------------------------------------------------------------------------
# Batch runner — used by the Celery task
# ---------------------------------------------------------------------------

def run_precedent_retrieval_for_all_high_clauses(
    high_clauses:  List[HighRiskClause],
    primary_model: str = "claude-sonnet-4-20250514",
) -> List[PrecedentMatch]:
    """
    Convenience wrapper: runs run_precedent_retrieval for each HIGH-risk clause.
    Processes sequentially; swap with asyncio.gather or ThreadPoolExecutor
    for parallel execution if needed.

    Args:
        high_clauses:  List of HIGH-risk clauses. LOW/MEDIUM clauses must be
                       filtered out by the caller (Celery task).
        primary_model: Anthropic model ID.

    Returns:
        List[PrecedentMatch] — one per input clause.
    """
    logger.info(
        "Running precedent retrieval for %d HIGH-risk clauses", len(high_clauses)
    )
    results = []
    for clause in high_clauses:
        match = run_precedent_retrieval(clause, primary_model)
        results.append(match)
    return results