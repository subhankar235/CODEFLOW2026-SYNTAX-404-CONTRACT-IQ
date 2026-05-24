"""services/ai/models package."""

from .openrouter_client import OpenRouterClient
from .model_config import PRIMARY_MODEL, FAST_MODEL

__all__ = ["OpenRouterClient", "PRIMARY_MODEL", "FAST_MODEL"]