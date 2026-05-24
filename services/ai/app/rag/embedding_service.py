"""
Embedding service for RAG pipeline (STEP 8.1).
Uses sentence-transformers with pgvector for contract Q&A embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Embedding model — all-MiniLM-L6-v2 (384 dimensions)
_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model: Optional[SentenceTransformer] = None


def _get_embedding_model() -> SentenceTransformer:
    """Lazy-load the sentence-transformer model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", _EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
    return _embedding_model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a text string.

    Parameters
    ----------
    text : str
        Text to embed.

    Returns
    -------
    List[float]
        384-dimensional embedding vector.
    """
    model = _get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def chunk_and_embed(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split text into chunks and embed each chunk.

    Parameters
    ----------
    text : str
        Text to process.
    chunk_size : int
        Chunk size in tokens.
    overlap : int
        Overlap in tokens.

    Returns
    -------
    List[Dict[str, Any]]
        List of {chunk_text, chunk_index, embedding_vector} objects.
    """
    from services.ai.app.utils.chunk_splitter import split_into_chunks

    chunks = split_into_chunks(text, chunk_size, overlap)
    result = []

    for i, chunk_text in enumerate(chunks):
        embedding = generate_embedding(chunk_text)
        result.append(
            {
                "chunk_text": chunk_text,
                "chunk_index": i,
                "embedding_vector": embedding,
            }
        )

    logger.info("Chunked text into %d chunks with embeddings", len(result))
    return result


def store_embeddings(
    contract_id: str,
    chunks_data: List[Dict[str, Any]],
    embedding_type: str = "contract_qa",
) -> None:
    """
    Store embeddings in pgvector embeddings table.

    Parameters
    ----------
    contract_id : str
        UUID of the contract.
    chunks_data : List[Dict[str, Any]]
        List of {chunk_text, chunk_index, embedding_vector} objects.
    embedding_type : str
        One of "contract_qa", "favorable_clause", "precedent".
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    # Use sync connection for simplicity in Celery task
    import os

    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg", "postgresql"
    )

    # Prepare data for bulk insert
    rows = []
    for chunk in chunks_data:
        embedding_str = "[" + ",".join(str(v) for v in chunk["embedding_vector"]) + "]"
        rows.append(
            (
                str(UUID(int=len(rows) + 1)),  # Generate UUID
                contract_id,
                chunk["chunk_text"],
                chunk["chunk_index"],
                embedding_type,
                embedding_str,
            )
        )

    # Bulk insert
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Use execute_values for efficient bulk insert
            from psycopg2.extras import execute_values

            execute_values(
                cur,
                """INSERT INTO embeddings (id, contract_id, text, chunk_index, embedding_type, embedding)
                   VALUES %s""",
                rows,
                template="(%s, %s, %s, %s, %s, %s::vector)",
            )
        conn.commit()

    logger.info("Stored %d embeddings for contract %s", len(rows), contract_id)
