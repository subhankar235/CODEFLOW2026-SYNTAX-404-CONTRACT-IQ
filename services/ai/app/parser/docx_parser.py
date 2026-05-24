"""
DOCX text extraction using python-docx.
Preserves heading structure and extracts table content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: F401 – kept for type hints
except ImportError as e:
    raise ImportError("python-docx is required: pip install python-docx") from e


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DOCXParseResult:
    text: str = ""
    section_count: int = 0
    error: Optional[str] = None
    success: bool = True


# ---------------------------------------------------------------------------
# Heading style helpers
# ---------------------------------------------------------------------------

# Built-in heading style names recognised by python-docx
_HEADING_STYLES: set[str] = {
    "heading 1", "heading 2", "heading 3",
    "heading 4", "heading 5", "heading 6",
    "title", "subtitle",
}

def _is_heading(para) -> bool:
    """Return True if the paragraph uses a heading style."""
    if para.style and para.style.name:
        return para.style.name.lower() in _HEADING_STYLES
    return False


def _heading_prefix(para) -> str:
    """Return a Markdown-style prefix for the heading level."""
    name = (para.style.name or "").lower()
    level_map = {
        "title": "#",
        "subtitle": "##",
        "heading 1": "#",
        "heading 2": "##",
        "heading 3": "###",
        "heading 4": "####",
        "heading 5": "#####",
        "heading 6": "######",
    }
    return level_map.get(name, "##")


# ---------------------------------------------------------------------------
# Table extractor
# ---------------------------------------------------------------------------

def _extract_table(table) -> str:
    """
    Render a docx Table as plain text.
    Columns are separated by '  |  ' and rows by newlines.
    """
    rows: list[str] = []
    for row in table.rows:
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        # Deduplicate merged cells (python-docx repeats text for merged cells)
        deduped: list[str] = []
        prev = object()
        for c in cells:
            if c != prev:
                deduped.append(c)
            prev = c
        rows.append("  |  ".join(deduped))
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Body XML child order helper
# ---------------------------------------------------------------------------

def _iter_block_items(doc: Document):
    """
    Yield (kind, obj) tuples in document body order where
    kind is 'paragraph' or 'table'.
    This preserves interleaved paragraphs and tables.
    """
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield "paragraph", Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield "table", Table(child, doc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_docx(file_path: str) -> DOCXParseResult:
    """
    Parse a DOCX file and return cleaned text.

    Parameters
    ----------
    file_path : local file path to the .docx file

    Returns
    -------
    DOCXParseResult with `.text`, `.section_count`, `.error`, `.success`
    """
    try:
        doc = Document(file_path)
    except Exception as exc:  # noqa: BLE001
        return DOCXParseResult(success=False, error=f"Cannot open DOCX: {exc}")

    chunks: list[str] = []
    section_count = 0

    try:
        for kind, obj in _iter_block_items(doc):
            if kind == "paragraph":
                para = obj
                raw_text = para.text  # full paragraph text incl. all runs

                if not raw_text.strip():
                    # Preserve a single blank line for paragraph separation
                    if chunks and chunks[-1] != "":
                        chunks.append("")
                    continue

                if _is_heading(para):
                    section_count += 1
                    prefix = _heading_prefix(para)
                    chunks.append(f"\n{prefix} {raw_text.strip()}\n")
                else:
                    chunks.append(raw_text.strip())

            elif kind == "table":
                table_text = _extract_table(obj)
                if table_text.strip():
                    chunks.append("\n[TABLE]\n" + table_text + "\n[/TABLE]\n")

    except Exception as exc:  # noqa: BLE001
        return DOCXParseResult(success=False, error=f"Error reading DOCX content: {exc}")

    # Join and clean
    full_text = "\n".join(chunks)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

    return DOCXParseResult(
        text=full_text,
        section_count=section_count,
        success=True,
    )