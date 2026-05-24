"""
<<<<<<< HEAD
services/ai/models/model_config.py
# This file just stores model names

Central registry of model identifiers used across the pipeline.
All values can be overridden via environment variables.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Model identifiers (OpenRouter format: provider/model-name)
# ---------------------------------------------------------------------------

# Primary model – used for complex analysis (risk, clauses, power asymmetry)
PRIMARY_MODEL: str = os.getenv(
    "PRIMARY_MODEL",
    "meta-llama/llama-3.3-70b-instruct",
)

# Fast model – used for lightweight tasks (type detection, summaries)
FAST_MODEL: str = os.getenv(
    "FAST_MODEL",
    "anthropic/claude-3-haiku",
)

# ---------------------------------------------------------------------------
# Request defaults
# ---------------------------------------------------------------------------

DEFAULT_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# ---------------------------------------------------------------------------
# Retry / backoff settings
# ---------------------------------------------------------------------------

MAX_RETRIES: int = 3
BACKOFF_BASE: float = 1.5   # seconds; actual wait = BACKOFF_BASE ** attempt
RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
=======
Model configuration constants for OpenRouter.
"""

PRIMARY_MODEL = "llama-3.3-70b-versatile"

FAST_MODEL = "llama-3.1-8b-instant"
>>>>>>> a06fb37f16f9d4bedfbfbd9a2038673103e5a1fa
