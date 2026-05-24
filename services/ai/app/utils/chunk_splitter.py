"""
Chunk splitter for RAG pipeline (STEP 8.1).
Splits text into overlapping chunks for embedding and retrieval.
"""

from typing import List


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.

    Parameters
    ----------
    text : str
        The text to split.
    chunk_size : int
        Approximate chunk size in tokens (estimate ~4 chars per token).
    overlap : int
        Number of tokens to overlap between adjacent chunks.

    Returns
    -------
    List[str]
        List of text chunks with overlap.
    """
    # Estimate characters per token (roughly 4 for English)
    chars_per_token = 4
    chunk_size_chars = chunk_size * chars_per_token
    overlap_chars = overlap * chars_per_token

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size_chars, len(text))

        # Try to break at sentence boundary if possible
        if end < len(text):
            # Look for sentence endings near the end
            for punct in [". ", "! ", "? ", "\n\n"]:
                pos = text.rfind(punct, start + chunk_size_chars - 200, end)
                if pos != -1:
                    end = pos + len(punct)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start with overlap
        start = max(start + 1, end - overlap_chars)

    return chunks


def get_chunk_with_context(
    chunks: List[str],
    index: int,
    context_chunks: int = 1,
) -> str:
    """
    Get a chunk with surrounding context.

    Parameters
    ----------
    chunks : List[str]
        All chunks.
    index : int
        Index of the target chunk.
    context_chunks : int
        Number of chunks to include before and after.

    Returns
    -------
    str
        Combined text with context.
    """
    start = max(0, index - context_chunks)
    end = min(len(chunks), index + context_chunks + 1)
    return " ".join(chunks[start:end])
