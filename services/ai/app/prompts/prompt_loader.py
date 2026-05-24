"""
Prompt loader utility for reading and substituting prompt templates.
"""

import os
import re
from typing import Optional

PROMPTS_DIR = os.path.dirname(__file__)


class PromptFileNotFoundError(Exception):
    """Raised when a prompt file does not exist."""
    pass


class MissingPlaceholderError(Exception):
    """Raised when a required placeholder is missing from values."""
    pass


def load_prompt(
    name: str,
    values: Optional[dict] = None,
    prompts_dir: Optional[str] = None,
) -> tuple[str, str]:
    """
    Load a prompt file and optionally substitute placeholders.

    Parameters
    ----------
    name : str
        Name of the prompt file (without .txt extension).
        E.g., "risk_analysis" for "risk_analysis.txt".
    values : dict, optional
        Dictionary of placeholder values for substitution.
        Keys should match {{placeholder}} tokens in the prompt.
    prompts_dir : str, optional
        Directory containing prompt files. Defaults to prompts directory.

    Returns
    -------
    tuple[str, str]
        (system_prompt, user_prompt)

    Raises
    ------
    PromptFileNotFoundError
        If the prompt file does not exist.
    MissingPlaceholderError
        If a required placeholder is missing from values.
    """
    prompt_dir = prompts_dir or PROMPTS_DIR
    file_path = os.path.join(prompt_dir, f"{name}.txt")

    if not os.path.exists(file_path):
        raise PromptFileNotFoundError(
            f"Prompt file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    system_prompt = ""
    user_prompt = ""

    current_section = None
    for line in content.split("\n"):
        if line.startswith("SYSTEM:"):
            current_section = "system"
            continue
        elif line.startswith("USER:"):
            current_section = "user"
            continue

        if current_section == "system":
            system_prompt += line + "\n"
        elif current_section == "user":
            user_prompt += line + "\n"

    system_prompt = system_prompt.strip()
    user_prompt = user_prompt.strip()

    if values:
        system_prompt = _substitute_placeholders(system_prompt, values, name)
        user_prompt = _substitute_placeholders(user_prompt, values, name)

    return system_prompt, user_prompt


def load_prompt_split(
    name: str,
    values: dict,
    prompts_dir: Optional[str] = None,
) -> dict:
    """
    Load a prompt and return a dict with 'system' and 'user' keys.

    Parameters
    ----------
    name : str
        Name of the prompt file.
    values : dict
        Placeholder values for substitution.
    prompts_dir : str, optional
        Directory containing prompt files.

    Returns
    -------
    dict
        {"system": "...", "user": "..."}
    """
    system, user = load_prompt(name, values, prompts_dir)
    return {"system": system, "user": user}


def split_system_user(prompt_content: str) -> tuple[str, str]:
    """
    Split combined prompt content into system and user parts.

    Parameters
    ----------
    prompt_content : str
        Full prompt content with SYSTEM: and USER: sections.

    Returns
    -------
    tuple[str, str]
        (system_prompt, user_prompt)
    """
    system_parts = []
    user_parts = []
    current_section = None

    for line in prompt_content.split("\n"):
        if line.startswith("SYSTEM:"):
            current_section = "system"
            continue
        elif line.startswith("USER:"):
            current_section = "user"
            continue

        if current_section == "system":
            system_parts.append(line)
        elif current_section == "user":
            user_parts.append(line)

    return (
        "\n".join(system_parts).strip(),
        "\n".join(user_parts).strip(),
    )


def _substitute_placeholders(prompt: str, values: dict, prompt_name: str) -> str:
    """
    Substitute all {{placeholder}} tokens with values.

    Parameters
    ----------
    prompt : str
        Prompt template with {{placeholder}} tokens.
    values : dict
        Dictionary of placeholder values.
    prompt_name : str
        Name of the prompt (for error messages).

    Returns
    -------
    str
        Prompt with substituted values.

    Raises
    ------
    MissingPlaceholderError
        If a required placeholder is missing.
    """
    placeholders = set(re.findall(r"\{\{(\w+)\}\}", prompt))

    missing = placeholders - set(values.keys())
    if missing:
        raise MissingPlaceholderError(
            f"Missing required placeholders {missing} for prompt '{prompt_name}'"
        )

    result = prompt
    for key, value in values.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))

    return result