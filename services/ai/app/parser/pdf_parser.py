"""
PDF text extraction using PyMuPDF (fitz).
Handles standard, multi-column, password-protected, and scanned PDFs.
"""

from __future__ import annotations

import re
import urllib.request
import tempfile
import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise ImportError("PyMuPDF is required: pip install pymupdf") from e


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PDFParseResult:
    text: str = ""
    page_count: int = 0
    needs_ocr: bool = False
    error: Optional[str] = None
    success: bool = True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def _download_to_tempfile(url: str) -> str:
    """Download URL to a temp file and return its path."""
    suffix = ".pdf"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    urllib.request.urlretrieve(url, tmp_path)  # noqa: S310 – controlled input
    return tmp_path


def _collect_repeated_lines(doc: fitz.Document, sample_pages: int = 5) -> set[str]:
    """
    Detect headers/footers by finding lines that appear on many pages.
    We sample up to `sample_pages` from the top and bottom of the document
    and flag any line that appears in ≥ 60 % of sampled pages.
    """
    total = len(doc)
    if total < 2:
        return set()

    # Grab text from the first and last few lines of each page
    from collections import Counter

    line_counter: Counter = Counter()
    pages_sampled = min(sample_pages, total)
    indices = list(range(pages_sampled)) + list(range(max(0, total - pages_sampled), total))
    indices = list(dict.fromkeys(indices))  # deduplicate while preserving order

    for i in indices:
        page = doc[i]
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        if not blocks:
            continue
        page_height = page.rect.height
        for blk in blocks:
            blk_text = blk[4].strip()
            if not blk_text:
                continue
            y_top = blk[1]
            y_bot = blk[3]
            # Consider block a header/footer candidate if in top/bottom 10 %
            if y_top < page_height * 0.10 or y_bot > page_height * 0.90:
                for ln in blk_text.splitlines():
                    ln = ln.strip()
                    if ln:
                        line_counter[ln] += 1

    threshold = max(2, int(len(indices) * 0.6))
    return {ln for ln, cnt in line_counter.items() if cnt >= threshold}


def _extract_page_text_reading_order(page: fitz.Page) -> str:
    """
    Extract text from a page in reading order.
    For multi-column layouts, PyMuPDF's 'blocks' are already sorted top-to-bottom
    left-to-right within each column.  We sort blocks by (top, left) to approximate
    Western reading order, then use 'dict' extraction for fine-grained span info.
    """
    blocks = page.get_text("blocks", sort=True)
    # sort=True already sorts by (y0, x0) which is reading order for most layouts
    lines: list[str] = []
    for blk in blocks:
        if blk[6] != 0:  # skip image blocks (type 1)
            continue
        txt = blk[4]
        if txt.strip():
            lines.append(txt.rstrip("\n"))
    return "\n".join(lines)


def _strip_repeated_lines(text: str, repeated: set[str]) -> str:
    """Remove lines that are known headers/footers."""
    if not repeated:
        return text
    cleaned: list[str] = []
    for line in text.splitlines():
        if line.strip() not in repeated:
            cleaned.append(line)
    return "\n".join(cleaned)


def _clean_text(text: str) -> str:
    """General post-processing: normalise whitespace while keeping paragraph breaks."""
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove trailing whitespace on each line
    text = "\n".join(ln.rstrip() for ln in text.splitlines())
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(source: str, password: Optional[str] = None) -> PDFParseResult:
    """
    Parse a PDF from a file path or URL.

    Parameters
    ----------
    source   : local file path or http(s) URL
    password : optional password for protected PDFs

    Returns
    -------
    PDFParseResult with `.text`, `.needs_ocr`, `.error`, `.success`
    """
    tmp_path: Optional[str] = None

    try:
        # ---- resolve source ------------------------------------------------
        if _is_url(source):
            tmp_path = _download_to_tempfile(source)
            file_path = tmp_path
        else:
            file_path = source

        # ---- open document -------------------------------------------------
        try:
            doc = fitz.open(file_path)
        except fitz.FileDataError as exc:
            return PDFParseResult(success=False, error=f"Cannot open PDF: {exc}")

        # ---- handle password -----------------------------------------------
        if doc.needs_pass:
            if password is None:
                doc.close()
                return PDFParseResult(
                    success=False,
                    error="PDF is password-protected. Provide the password via the `password` argument.",
                )
            authenticated = doc.authenticate(password)
            if not authenticated:
                doc.close()
                return PDFParseResult(
                    success=False,
                    error="Incorrect password for the PDF.",
                )

        page_count = len(doc)

        # ---- detect scanned PDF (no extractable text) ----------------------
        total_chars = sum(len(doc[i].get_text()) for i in range(min(5, page_count)))
        if total_chars < 20 and page_count > 0:
            doc.close()
            return PDFParseResult(
                text="",
                page_count=page_count,
                needs_ocr=True,
                success=True,
                error=None,
            )

        # ---- detect repeated headers/footers --------------------------------
        repeated_lines = _collect_repeated_lines(doc)

        # ---- extract text page by page -------------------------------------
        all_pages: list[str] = []
        for page_num in range(page_count):
            page = doc[page_num]
            page_text = _extract_page_text_reading_order(page)
            page_text = _strip_repeated_lines(page_text, repeated_lines)
            if page_text.strip():
                all_pages.append(page_text)

        doc.close()

        full_text = "\n\n".join(all_pages)
        full_text = _clean_text(full_text)

        return PDFParseResult(
            text=full_text,
            page_count=page_count,
            needs_ocr=False,
            success=True,
        )

    except Exception as exc:  # noqa: BLE001
        return PDFParseResult(success=False, error=f"Unexpected error: {exc}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)