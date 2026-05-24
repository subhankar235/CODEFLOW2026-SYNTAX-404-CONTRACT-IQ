"""
Vector store for RAG (pgvector implementation).
STEPS_BACKEND.md §8.1 — uses pgvector in PostgreSQL.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def store_embeddings(
    contract_id: str,
    chunks: List[Dict[str, Any]],
    embedding_type: str = "contract_qa",
) -> None:
    """
    Store embeddings in pgvector embeddings table.

    Parameters
    ----------
    contract_id : str
        UUID of the contract.
    chunks : List[Dict[str, Any]]
        List of {chunk_text, chunk_index, embedding_vector} objects.
    embedding_type : str
        One of "contract_qa", "favorable_clause", "precedent".
    """
    import psycopg2
    from psycopg2.extras import execute_values
    import os

    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg", "postgresql"
    )

    # Prepare data for bulk insert
    rows = []
    for chunk in chunks:
        embedding_str = "[" + ",".join(str(v) for v in chunk["embedding_vector"]) + "]"
        rows.append(
            (
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
            execute_values(
                cur,
                """INSERT INTO embeddings (contract_id, text, chunk_index, embedding_type, embedding)
                   VALUES %s""",
                rows,
                template="(%s, %s, %s, %s, %s::vector)",
            )
        conn.commit()

    logger.info("Stored %d embeddings for contract %s", len(rows), contract_id)


def search_similar_chunks(
    query_embedding: List[float],
    contract_id: str,
    top_k: int = 5,
) -> List[str]:
    """
    Search for similar chunks in pgvector.

    Parameters
    ----------
    query_embedding : List[float]
        The query embedding vector.
    contract_id : str
        UUID of the contract to search within.
    top_k : int
        Number of results to return.

    Returns
    -------
    List[str]
        List of chunk texts.
    """
    import psycopg2
    import os

    db_url = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg", "postgresql"
    )
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT text FROM embeddings
                   WHERE contract_id = %s AND embedding_type = 'contract_qa'
                   ORDER BY embedding <=> %s::vector
                   LIMIT %s""",
                (contract_id, embedding_str, top_k),
            )
            rows = cur.fetchall()

    return [row[0] for row in rows] if rows else []
