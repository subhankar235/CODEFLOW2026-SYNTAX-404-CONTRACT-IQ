"""
services/ai/utils/confidence_scorer.py
---------------------------------------
Confidence Score Calculator.

What this file does:
  Provides a single static method, ConfidenceScorer.compute(), that fuses two
  independent confidence signals into one final score (0–100):

    1. RAG retrieval similarity  – the average cosine similarity returned by
       pgvector for the top-k precedent documents (float, 0–1).
    2. LLM self-rated confidence – the integer the LLM places in its JSON
       response under the key "llm_confidence" (int, 0–100).

  Final score formula:
      final = (avg_similarity * llm_confidence_normalised) * 100
            = avg_similarity  *  (llm_confidence / 100)   * 100

  Conceptually this means:
    - Perfect retrieval + perfect LLM confidence → 100
    - Poor retrieval (similarity 0.3) + high LLM confidence (90) → 27
    - Good retrieval (similarity 0.85) + moderate LLM (70) → 59.5

  The result is clamped to [0, 100] and rounded to two decimal places.
"""

from __future__ import annotations


class ConfidenceScorer:
    """Static helper for fused RAG × LLM confidence scoring."""

    @staticmethod
    def compute(avg_retrieval_similarity: float, llm_confidence: float) -> float:
        """
        Compute the final confidence score.

        Parameters
        ----------
        avg_retrieval_similarity:
            Mean cosine similarity of the top-k retrieved documents (0.0–1.0).
            Values outside [0, 1] are clamped before computation.
        llm_confidence:
            The LLM's self-rated confidence extracted from its JSON response
            (0–100 integer scale).  Values outside [0, 100] are clamped.

        Returns
        -------
        float in [0.0, 100.0], rounded to 2 decimal places.
        """
        # Clamp inputs to valid ranges
        similarity = max(0.0, min(1.0, float(avg_retrieval_similarity)))
        llm_conf_norm = max(0.0, min(100.0, float(llm_confidence))) / 100.0

        raw_score = similarity * llm_conf_norm * 100.0
        return round(max(0.0, min(100.0, raw_score)), 2)

    @staticmethod
    def validate(score: float) -> bool:
        """Return True if *score* is a valid confidence score (0–100)."""
        return 0.0 <= score <= 100.0