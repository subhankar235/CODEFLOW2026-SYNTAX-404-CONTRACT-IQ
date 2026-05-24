"""
Translation using deep-translator (free, no API key required).
Uses Google Translate as backend.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _load_legal_glossary() -> Dict[str, Dict[str, str]]:
    """Load legal glossary from JSON file."""
    import json
    from pathlib import Path

    glossary_path = Path(__file__).parent / "legal_glossary.json"
    if not glossary_path.exists():
        logger.warning("legal_glossary.json not found at %s", glossary_path)
        return {}

    try:
        return json.loads(glossary_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to load legal glossary: %s", e)
        return {}


# Cache glossary
_legal_glossary = None


def _get_glossary() -> Dict[str, Dict[str, str]]:
    """Get cached legal glossary."""
    global _legal_glossary
    if _legal_glossary is None:
        _legal_glossary = _load_legal_glossary()
    return _legal_glossary


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """
    Translate a single text string from source to target language.

    Parameters
    ----------
    text : str
        Text to translate.
    source_lang : str
        Source language code (e.g., "en", "es").
    target_lang : str
        Target language code (e.g., "en", "es").

    Returns
    -------
    str
        Translated text with legal glossary applied.
    """
    if source_lang == target_lang:
        return text

    if target_lang == "en":
        if source_lang == "en":
            return text

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)

        translated = _apply_legal_glossary(translated, target_lang)

        return translated

    except Exception as e:
        logger.error("Google translation failed: %s", e)
        return text


def translate_batch(
    texts: List[str],
    source_lang: str,
    target_lang: str,
) -> List[str]:
    """
    Translate multiple texts.

    Parameters
    ----------
    texts : List[str]
        List of texts to translate.
    source_lang : str
        Source language code.
    target_lang : str
        Target language code.

    Returns
    -------
    List[str]
        List of translated texts.
    """
    if source_lang == target_lang:
        return texts

    try:
        from deep_translator import GoogleTranslator
        translated = []
        for text in texts:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            translated.append(result)

        glossary = _get_glossary()
        if glossary and target_lang in glossary:
            translated = [_apply_legal_glossary(t, target_lang) for t in translated]

        return translated

    except Exception as e:
        logger.error("Google batch translation failed: %s", e)
        return texts


def translate_to_english(text: str, source_lang: str) -> str:
    """Translate text to English."""
    return translate_text(text, source_lang, "en")


def translate_from_english(text: str, target_lang: str) -> str:
    """Translate text from English to target language."""
    return translate_text(text, "en", target_lang)


def _apply_legal_glossary(text: str, target_lang: str) -> str:
    """Apply legal glossary replacements to translated text."""
    glossary = _get_glossary()
    if not glossary or target_lang not in glossary:
        return text

    result = text
    for term_data in glossary.get(target_lang, []):
        if "original" in term_data and "translation" in term_data:
            result = result.replace(
                term_data["original"],
                term_data["translation"],
            )

    return result


def translate_to_english(text: str, source_language: str) -> str:
    """Translate text from source language to English."""
    if source_language == "en":
        return text
    return translate_text(text, source_language, "en")


def translate_from_english(text: str, target_language: str) -> str:
    """Translate text from English to target language."""
    if target_language == "en":
        return text
    return translate_text(text, "en", target_language)