"""
Fallback document parser using unstructured[pdf,docx].
Used when primary parsers return insufficient text (e.g. scanned PDFs).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from unstructured.partition.auto import partition


def _get_partition():
    """Lazy import of unstructured partition function."""
    try:
        from unstructured.partition.auto import partition
        return partition
    except ImportError as e:
        raise ImportError(
            "unstructured is required: pip install 'unstructured[pdf,docx]'"
        ) from e


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class FallbackParseResult:
    text: str = ""
    element_count: int = 0
    error: Optional[str] = None
    success: bool = True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_with_fallback(file_path: str, file_type: Optional[str] = None) -> FallbackParseResult:
    """
    Parse a document using the unstructured library.

    Parameters
    ----------
    file_path : local file path to the document
    file_type : optional hint – 'pdf' or 'docx'.  If omitted, unstructured
                auto-detects from the file extension / magic bytes.

    Returns
    -------
    FallbackParseResult with `.text`, `.element_count`, `.error`, `.success`
    """
    try:
        kwargs: dict = {"filename": file_path}
        if file_type:
            # unstructured uses content_type or strategy hints
            mime_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
            ct = mime_map.get(file_type.lower().lstrip("."))
            if ct:
                kwargs["content_type"] = ct

        partition = _get_partition()
        elements = partition(**kwargs)
    except Exception as exc:  # noqa: BLE001
        return FallbackParseResult(success=False, error=f"unstructured partition failed: {exc}")

    if not elements:
        return FallbackParseResult(text="", element_count=0, success=True)

    # Convert elements to text, preserving natural order
    lines: list[str] = []
    for el in elements:
        txt = str(el).strip()
        if txt:
            lines.append(txt)

    full_text = "\n\n".join(lines)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

    return FallbackParseResult(
        text=full_text,
        element_count=len(elements),
        success=True,
    )