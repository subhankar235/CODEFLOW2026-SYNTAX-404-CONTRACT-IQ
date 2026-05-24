"""
Embedder for contract Q&A RAG (STEP 8.1).
Implements the contract embedding function using sentence-transformers + pgvector.
"""

import logging
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Embedding model - all-MiniLM-L6-v2 (384 dimensions)
_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
_embedding_model = None


def _get_embedding_model() -> SentenceTransformer:
    """Lazy-load the sentence-transformer model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", _EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
    return _embedding_model


def embed_text(text: str) -> List[float]:
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
        Chunk size in tokens (roughly 4 chars per token).
    overlap : int
        Overlap in tokens between adjacent chunks.

    Returns
    -------
    List[Dict[str, Any]]
        List of {chunk_text, chunk_index, embedding_vector} objects.
    """
    from services.ai.app.utils.chunk_splitter import split_into_chunks

    chunks = split_into_chunks(text, chunk_size, overlap)
    result = []

    for i, chunk_text in enumerate(chunks):
        embedding = embed_text(chunk_text)
        result.append(
            {
                "chunk_text": chunk_text,
                "chunk_index": i,
                "embedding_vector": embedding,
            }
        )

    logger.info("Chunked text into %d chunks with embeddings", len(result))
    return result
