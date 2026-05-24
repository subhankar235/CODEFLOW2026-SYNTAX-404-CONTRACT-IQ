"""
services/ai/parser/__init__.py
Unified document parsing dispatcher.

Priority:
  1. Primary parser  (PyMuPDF for PDF, python-docx for DOCX)
  2. Fallback parser (unstructured) if primary returns < MIN_CHARS characters
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .pdf_parser import parse_pdf, PDFParseResult
from .docx_parser import parse_docx, DOCXParseResult
from .fallback_parser import parse_with_fallback, FallbackParseResult

# Minimum characters considered "meaningful" text from a primary parser
MIN_CHARS: int = 100


# ---------------------------------------------------------------------------
# Unified result
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    text: str = ""
    file_type: str = ""
    parser_used: str = ""          # 'pdf', 'docx', 'fallback'
    needs_ocr: bool = False
    page_count: int = 0            # PDF only
    section_count: int = 0         # DOCX only
    error: Optional[str] = None
    success: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_file_type(file_path: str) -> str:
    """Return lowercase extension without the dot, e.g. 'pdf' or 'docx'."""
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip(".")


def _text_is_meaningful(text: str) -> bool:
    return len(text.strip()) >= MIN_CHARS


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def parse_document(
    file_path: str,
    password: Optional[str] = None,
    file_type: Optional[str] = None,
) -> ParseResult:
    """
    Parse a document using the best available parser.

    Parameters
    ----------
    file_path  : local path (URLs should be pre-downloaded, or use pdf_parser directly)
    password   : optional password for protected PDFs
    file_type  : optional override – 'pdf' or 'docx'.  Detected from extension if omitted.

    Returns
    -------
    ParseResult with unified fields regardless of which parser was used.
    """
    ftype = (file_type or _detect_file_type(file_path)).lower().lstrip(".")

    # ------------------------------------------------------------------ PDF
    if ftype == "pdf":
        primary: PDFParseResult = parse_pdf(file_path, password=password)

        if not primary.success:
            # Hard failure (wrong password, corrupt file) – do not attempt fallback
            return ParseResult(
                file_type="pdf",
                parser_used="pdf",
                page_count=primary.page_count,
                needs_ocr=primary.needs_ocr,
                error=primary.error,
                success=False,
            )

        if primary.needs_ocr or not _text_is_meaningful(primary.text):
            # Primary extracted too little – try unstructured fallback
            fallback: FallbackParseResult = parse_with_fallback(file_path, "pdf")
            if fallback.success and _text_is_meaningful(fallback.text):
                return ParseResult(
                    text=fallback.text,
                    file_type="pdf",
                    parser_used="fallback",
                    page_count=primary.page_count,
                    needs_ocr=primary.needs_ocr,
                    success=True,
                )
            # Fallback also failed or returned nothing
            return ParseResult(
                text=primary.text,          # could be ""
                file_type="pdf",
                parser_used="fallback" if fallback.success else "pdf",
                page_count=primary.page_count,
                needs_ocr=primary.needs_ocr,
                error=fallback.error if not fallback.success else None,
                success=fallback.success,
            )

        # Primary succeeded with meaningful text
        return ParseResult(
            text=primary.text,
            file_type="pdf",
            parser_used="pdf",
            page_count=primary.page_count,
            needs_ocr=False,
            success=True,
        )

    # ----------------------------------------------------------------- DOCX
    if ftype in ("docx", "doc"):
        primary_docx: DOCXParseResult = parse_docx(file_path)

        if not primary_docx.success:
            return ParseResult(
                file_type="docx",
                parser_used="docx",
                error=primary_docx.error,
                success=False,
            )

        if not _text_is_meaningful(primary_docx.text):
            fallback_docx: FallbackParseResult = parse_with_fallback(file_path, "docx")
            if fallback_docx.success and _text_is_meaningful(fallback_docx.text):
                return ParseResult(
                    text=fallback_docx.text,
                    file_type="docx",
                    parser_used="fallback",
                    section_count=primary_docx.section_count,
                    success=True,
                )
            return ParseResult(
                text=primary_docx.text,
                file_type="docx",
                parser_used="fallback" if fallback_docx.success else "docx",
                section_count=primary_docx.section_count,
                error=fallback_docx.error if not fallback_docx.success else None,
                success=fallback_docx.success,
            )

        return ParseResult(
            text=primary_docx.text,
            file_type="docx",
            parser_used="docx",
            section_count=primary_docx.section_count,
            success=True,
        )

    # -------------------------------------------------------- Unknown type
    # Last resort: let unstructured try
    fallback_gen: FallbackParseResult = parse_with_fallback(file_path, ftype)
    return ParseResult(
        text=fallback_gen.text,
        file_type=ftype,
        parser_used="fallback",
        error=fallback_gen.error,
        success=fallback_gen.success,
    )