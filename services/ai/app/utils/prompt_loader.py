"""
services/ai/utils/prompt_loader.py

Reads prompt template files and performs {{placeholder}} substitution.
All pipeline modules should use this loader — never read prompt files directly.
"""

from __future__ import annotations

import re
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default directory containing the .txt prompt templates
_DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Regex that finds every {{placeholder}} token in a template
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PromptFileNotFoundError(FileNotFoundError):
    """Raised when the requested prompt template file does not exist."""


class MissingPlaceholderError(KeyError):
    """Raised when the substitution dict is missing a required placeholder."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=64)
def _read_template(file_path: str) -> str:
    """Read and cache a prompt template file by absolute path."""
    return Path(file_path).read_text(encoding="utf-8")


def _resolve_path(name: str, prompts_dir: Path) -> Path:
    """
    Resolve a prompt name to a .txt file path.
    `name` may include or omit the .txt extension.
    """
    if not name.endswith(".txt"):
        name = f"{name}.txt"
    return prompts_dir / name


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_prompt(
    name: str,
    variables: dict[str, str],
    prompts_dir: Optional[str | Path] = None,
) -> str:
    """
    Load a prompt template by name and substitute ``{{placeholder}}`` tokens.

    Parameters
    ----------
    name        : template file name, with or without the .txt extension
                  e.g. ``"risk_analysis"`` or ``"risk_analysis.txt"``
    variables   : mapping of placeholder name → replacement value
    prompts_dir : directory containing the prompt files
                  (defaults to ``services/ai/prompts/``)

    Returns
    -------
    The fully rendered prompt string.

    Raises
    ------
    PromptFileNotFoundError   : if the template file does not exist
    MissingPlaceholderError   : if a ``{{token}}`` found in the template
                                has no corresponding key in ``variables``
    """
    base_dir = Path(prompts_dir) if prompts_dir else _DEFAULT_PROMPTS_DIR
    file_path = _resolve_path(name, base_dir)

    if not file_path.exists():
        raise PromptFileNotFoundError(
            f"Prompt template not found: {file_path}. "
            f"Available templates: {_list_available(base_dir)}"
        )

    template = _read_template(str(file_path))

    # Find all required placeholders in the template
    required = set(_PLACEHOLDER_RE.findall(template))

    # Check for missing keys
    provided = set(variables.keys())
    missing = required - provided
    if missing:
        raise MissingPlaceholderError(
            f"Prompt '{name}' requires placeholder(s) {sorted(missing)} "
            f"but they were not provided. "
            f"Provided keys: {sorted(provided)}"
        )

    # Perform substitution – only replace tokens that exist in the template
    def _replacer(match: re.Match) -> str:
        key = match.group(1)
        return str(variables[key])

    rendered = _PLACEHOLDER_RE.sub(_replacer, template)
    return rendered


def split_system_user(rendered_prompt: str) -> tuple[str, str]:
    """
    Split a rendered prompt into (system_prompt, user_prompt) using the
    ``SYSTEM:`` / ``USER:`` section markers written in every .txt template.

    Returns
    -------
    (system_text, user_text) – both stripped of leading/trailing whitespace.
    If no markers are found, the entire text is returned as the user prompt
    with an empty system prompt.
    """
    system_marker = "SYSTEM:"
    user_marker = "USER:"

    sys_idx = rendered_prompt.find(system_marker)
    usr_idx = rendered_prompt.find(user_marker)

    if sys_idx == -1 and usr_idx == -1:
        return "", rendered_prompt.strip()

    if sys_idx != -1 and usr_idx != -1:
        system_text = rendered_prompt[sys_idx + len(system_marker):usr_idx].strip()
        user_text = rendered_prompt[usr_idx + len(user_marker):].strip()
        return system_text, user_text

    if sys_idx != -1:
        return rendered_prompt[sys_idx + len(system_marker):].strip(), ""

    # Only USER: present
    return "", rendered_prompt[usr_idx + len(user_marker):].strip()


def load_prompt_split(
    name: str,
    variables: dict[str, str],
    prompts_dir: Optional[str | Path] = None,
) -> tuple[str, str]:
    """
    Convenience wrapper: load + substitute + split into (system, user).

    Returns
    -------
    (system_prompt, user_prompt) ready to pass to the LLM client.
    """
    rendered = load_prompt(name, variables, prompts_dir)
    return split_system_user(rendered)


def _list_available(directory: Path) -> list[str]:
    """Return sorted list of .txt template names in the given directory."""
    if not directory.exists():
        return []
    return sorted(p.stem for p in directory.glob("*.txt"))


def invalidate_cache() -> None:
    """Clear the template file cache (useful in tests)."""
    _read_template.cache_clear()