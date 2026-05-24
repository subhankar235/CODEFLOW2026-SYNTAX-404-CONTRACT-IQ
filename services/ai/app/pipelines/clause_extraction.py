"""
services/ai/pipelines/clause_extraction.py

Clause segmentation using spaCy en_core_web_sm.

Rules
-----
* Split contract text into sentence units via spaCy.
* Group sentences that are continuations of the same numbered/lettered clause.
* Merge clauses < 10 words into their neighbour.
* Split clauses > 500 words at sentence boundaries.
* Return list of clause dicts: clause_id, position_index, text, word_count.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

try:
    import spacy
except ImportError as e:
    raise ImportError("spaCy is required: pip install spacy") from e


# ---------------------------------------------------------------------------
# spaCy model loader (cached module-level)
# ---------------------------------------------------------------------------

_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            )
        if "sentencizer" not in _NLP.pipe_names:
            _NLP.add_pipe("sentencizer")
    return _NLP


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches clause starters like: 1. / 1.1 / 1.1.1 / (a) / a. / A.
_CLAUSE_HEADER = re.compile(
    r"^\s*"
    r"(?:"
    r"\d+(?:\.\d+)*\.?"         # 1  /  1.1  /  1.1.2.
    r"|"
    r"\([a-zA-Z0-9]+\)"         # (a)  (i)  (1)
    r"|"
    r"[A-Za-z]\."               # a.  B.
    r")"
    r"\s"
)

# A sentence is a "hanging continuation" if it does NOT start with a capital
# letter (suggesting it finishes the previous clause's thought).
_STARTS_LOWERCASE = re.compile(r"^\s*[a-z]")


# ---------------------------------------------------------------------------
# Step 1 — sentence extraction
# ---------------------------------------------------------------------------

def _extract_sentences(text: str) -> list[str]:
    """Use spaCy to split text into sentences."""
    nlp = _get_nlp()
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


# ---------------------------------------------------------------------------
# Step 2 — group sentences into logical clauses
# ---------------------------------------------------------------------------

def _group_into_clauses(sentences: list[str]) -> list[str]:
    """
    Group adjacent sentences that belong to the same clause.

    A new clause boundary is opened when:
      - The sentence starts with a numbered/lettered clause header (1.2, (a), etc.)
      - The sentence starts with a capital letter after a sentence that ended with '.'
        (i.e. it is clearly a new thought).

    A sentence is merged into the *previous* clause when:
      - It starts with a lowercase letter (continuation).
      - It is a very short fragment (< 5 words) that doesn't look like a new header.
    """
    if not sentences:
        return []

    groups: list[list[str]] = [[sentences[0]]]

    for sent in sentences[1:]:
        is_header = bool(_CLAUSE_HEADER.match(sent))
        is_lowercase_start = bool(_STARTS_LOWERCASE.match(sent))
        word_count = len(sent.split())
        is_tiny_fragment = word_count < 5 and not is_header

        if is_header:
            # Always start a new clause on a numbered/lettered header
            groups.append([sent])
        elif is_lowercase_start or is_tiny_fragment:
            # Continuation: merge into previous group
            groups[-1].append(sent)
        else:
            # Capital-letter sentence after a previous clause – new clause
            groups.append([sent])

    return [" ".join(g) for g in groups]


# ---------------------------------------------------------------------------
# Step 3 — enforce word-count constraints
# ---------------------------------------------------------------------------

def _word_count(text: str) -> int:
    return len(text.split())


def _merge_short_clauses(clauses: list[str], min_words: int = 10) -> list[str]:
    """
    Merge clauses shorter than `min_words` into the adjacent clause.
    Prefer merging forward (next clause); if last clause, merge backward.
    """
    if not clauses:
        return clauses

    result: list[str] = list(clauses)
    changed = True
    while changed:
        changed = False
        new_result: list[str] = []
        i = 0
        while i < len(result):
            current = result[i]
            if _word_count(current) < min_words:
                if i + 1 < len(result):
                    # Merge forward
                    result[i + 1] = current + " " + result[i + 1]
                    changed = True
                    i += 1
                    continue
                elif new_result:
                    # Merge backward
                    new_result[-1] = new_result[-1] + " " + current
                    changed = True
                    i += 1
                    continue
            new_result.append(current)
            i += 1
        result = new_result

    return result


def _split_long_clauses(clauses: list[str], max_words: int = 500) -> list[str]:
    """
    Split clauses over `max_words` at sentence boundaries.
    Uses spaCy for sentence splitting within the long clause.
    """
    result: list[str] = []
    for clause in clauses:
        if _word_count(clause) <= max_words:
            result.append(clause)
            continue

        # Re-split this clause into sentences and re-chunk greedily
        sentences = _extract_sentences(clause)
        chunk: list[str] = []
        chunk_wc = 0
        for sent in sentences:
            wc = _word_count(sent)
            if chunk_wc + wc > max_words and chunk:
                result.append(" ".join(chunk))
                chunk = [sent]
                chunk_wc = wc
            else:
                chunk.append(sent)
                chunk_wc += wc
        if chunk:
            result.append(" ".join(chunk))

    return result


# ---------------------------------------------------------------------------
# Step 4 — build final clause objects
# ---------------------------------------------------------------------------

def _build_clause_objects(clauses: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "clause_id": str(uuid.uuid4()),
            "position_index": idx,
            "text": clause.strip(),
            "word_count": _word_count(clause),
        }
        for idx, clause in enumerate(clauses)
        if clause.strip()
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def segment_clauses(
    text: str,
    min_words: int = 10,
    max_words: int = 500,
) -> list[dict[str, Any]]:
    """
    Segment contract text into logical clauses.

    Parameters
    ----------
    text      : full contract text (output of parse_document)
    min_words : clauses below this threshold are merged
    max_words : clauses above this threshold are split

    Returns
    -------
    List of dicts, each containing:
      - clause_id      : UUID string
      - position_index : sequential int (0-based, no gaps)
      - text           : clause text
      - word_count     : int
    """
    if not text or not text.strip():
        return []

    # 1. Sentence-level units
    sentences = _extract_sentences(text)

    # 2. Group into logical clauses
    raw_clauses = _group_into_clauses(sentences)

    # 3. Enforce size constraints
    raw_clauses = _merge_short_clauses(raw_clauses, min_words=min_words)
    raw_clauses = _split_long_clauses(raw_clauses, max_words=max_words)

    # 4. Final merge pass in case splitting created tiny tails
    raw_clauses = _merge_short_clauses(raw_clauses, min_words=min_words)

    # 5. Build result objects
    return _build_clause_objects(raw_clauses)