"""services/ai/app/utils package."""
from .prompt_loader import load_prompt, load_prompt_split, split_system_user, PromptFileNotFoundError, MissingPlaceholderError

# validate_llm_response lives at services/ai/schemas/ (not services/ai/app/schemas/)
# Import using the top-level package path so it resolves correctly regardless
# of how the AI service is run (uvicorn from repo root vs. from services/ai/).
try:
    from services.ai.schemas.validate_llm_response import (
        validate_llm_response,
        validate_risk_analysis,
        validate_type_detection,
        validate_consequence,
        validate_summary,
        validate_power_asymmetry,
        validate_counter_offer,
        validate_precedent,
    )
except ImportError:
    # Fallback: when running from inside services/ai/ as the working directory
    from schemas.validate_llm_response import (  # type: ignore[no-redef]
        validate_llm_response,
        validate_risk_analysis,
        validate_type_detection,
        validate_consequence,
        validate_summary,
        validate_power_asymmetry,
        validate_counter_offer,
        validate_precedent,
    )

__all__ = [
    "load_prompt", "load_prompt_split", "split_system_user",
    "PromptFileNotFoundError", "MissingPlaceholderError",
    "validate_llm_response",
    "validate_risk_analysis", "validate_type_detection", "validate_consequence",
    "validate_summary", "validate_power_asymmetry", "validate_counter_offer",
    "validate_precedent",
]