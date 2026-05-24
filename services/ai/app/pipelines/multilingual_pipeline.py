"""
Multilingual Pipeline (STEP 9.2).
Implements preprocess_contract() and postprocess_results() for translation.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "hi"]


def preprocess_contract(
    contract_text: str,
) -> Dict[str, Any]:
    """
    Preprocess contract: detect language, translate to English if needed.

    Parameters
    ----------
    contract_text : str
        Original contract text.

    Returns
    -------
    Dict[str, Any]
        {
            "english_text": str,  # Translated to English if needed
            "original_language": str,  # Detected language
            "was_translated": bool,  # True if translation occurred
        }
    """
    from services.ai.app.multilingual.language_detector import detect_language

    original_language = detect_language(contract_text)
    logger.info("Detected language: %s", original_language)

    if original_language not in SUPPORTED_LANGUAGES:
        logger.warning("Unsupported language: %s, treating as 'en'", original_language)
        original_language = "en"

    if original_language == "en":
        return {
            "english_text": contract_text,
            "original_language": "en",
            "was_translated": False,
        }

    # Translate to English
    from services.ai.app.multilingual.translator import translate_text

    try:
        english_text = translate_text(contract_text, original_language, "en")
        logger.info("Translated contract from %s to English", original_language)
        return {
            "english_text": english_text,
            "original_language": original_language,
            "was_translated": True,
        }
    except Exception as e:
        logger.error("Translation to English failed: %s", e)
        return {
            "english_text": contract_text,  # Fallback to original
            "original_language": original_language,
            "was_translated": False,
        }


def postprocess_results(
    clause_results: List[Dict[str, Any]],
    analysis_result: Dict[str, Any],
    target_language: str,
) -> Dict[str, Any]:
    """
    Translate results back to target language after analysis.

    Parameters
    ----------
    clause_results : List[Dict[str, Any]]
        List of clause result dicts with fields to translate.
    analysis_result : Dict[str, Any]
        Analysis result with summary fields to translate.
    target_language : str
        Target language code.

    Returns
    -------
    Dict[str, Any]
        {
            "clause_results": List[Dict[str, Any]],  # Translated clause results
            "analysis_result": Dict[str, Any],  # Translated analysis result
        }
    """
    if target_language == "en":
        return {
            "clause_results": clause_results,
            "analysis_result": analysis_result,
        }

    logger.info("Translating results to %s", target_language)

    from services.ai.app.multilingual.translator import translate_batch

    # Collect all texts to translate in batch
    texts_to_translate = []
    text_indices = []  # Track which text belongs to which field

    # Process clause results
    translated_clauses = []
    for clause in clause_results:
        translated_clause = clause.copy()

        # Fields to translate
        for field in ["plain_english", "worst_case_scenario", "headline", "scenario"]:
            if field in clause and clause[field]:
                translated_clause[field] = translate_text_field(
                    clause[field], "en", target_language
                )

        translated_clauses.append(translated_clause)

    # Process analysis result
    translated_analysis = analysis_result.copy() if analysis_result else {}

    if analysis_result:
        # Translate top_3_concerns
        if "top_3_concerns" in analysis_result:
            translated_analysis["top_3_concerns"] = [
                translate_text_field(c, "en", target_language)
                for c in analysis_result.get("top_3_concerns", [])
            ]

        # Translate top_2_positives
        if "top_2_positives" in analysis_result:
            translated_analysis["top_2_positives"] = [
                translate_text_field(p, "en", target_language)
                for p in analysis_result.get("top_2_positives", [])
            ]

        # Translate one_liner
        if "one_liner" in analysis_result:
            translated_analysis["one_liner"] = translate_text_field(
                analysis_result["one_liner"], "en", target_language
            )

    logger.info("Translation to %s complete", target_language)

    return {
        "clause_results": translated_clauses,
        "analysis_result": translated_analysis,
    }


def translate_text_field(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """Translate a single text field."""
    if not text:
        return text

    from services.ai.app.multilingual.translator import translate_text

    try:
        return translate_text(text, source_lang, target_lang)
    except Exception as e:
        logger.error("Failed to translate field: %s", e)
        return text  # Return original on failure
