from fastapi import APIRouter
from pydantic import BaseModel

from app.multilingual.language_detector import detect_language
from app.multilingual.translator import (
    translate_to_english,
    translate_from_english,
)

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "en"


@router.post("/translate")
async def translate(req: TranslateRequest):

    detected_language = detect_language(req.text)

    if req.target_language == "en":

        translated = translate_to_english(
            req.text,
            detected_language
        )

    else:

        english_text = translate_to_english(
            req.text,
            detected_language
        )

        translated = translate_from_english(
            english_text,
            req.target_language
        )

    return {
        "original_text": req.text,
        "detected_language": detected_language,
        "translated_text": translated,
        "target_language": req.target_language
    }