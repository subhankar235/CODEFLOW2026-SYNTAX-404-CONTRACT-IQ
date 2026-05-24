"""
Step 6.2 — Risk Mapper
Maps clause text through the regex rule engine and produces a triage level:
  GREEN  — 0 matches
  YELLOW — 1–2 matches (and no HIGH-level pattern triggered)
  RED    — 3+ matches  OR  any single HIGH-level pattern match
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .regex_rules import ALL_PATTERNS, RiskLevel, RiskPattern

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Triage level
# ---------------------------------------------------------------------------

class TriageLevel(str, Enum):
    GREEN  = "GREEN"
    YELLOW = "YELLOW"
    RED    = "RED"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RiskMapperResult:
    """Outcome of running the rule engine on a single clause."""

    triage: TriageLevel
    match_count: int
    triggered_patterns: List[RiskPattern] = field(default_factory=list)
    high_level_triggers: List[RiskPattern] = field(default_factory=list)

    # Convenience summaries for downstream consumers
    @property
    def categories(self) -> List[str]:
        return list({p.category.value for p in self.triggered_patterns})

    @property
    def preliminary_risk_level(self) -> Optional[str]:
        """Highest preliminary risk level among triggered patterns, or None."""
        if self.high_level_triggers:
            return RiskLevel.HIGH.value
        if self.triggered_patterns:
            return RiskLevel.MEDIUM.value
        return None

    def to_dict(self) -> dict:
        return {
            "triage": self.triage.value,
            "match_count": self.match_count,
            "categories": self.categories,
            "preliminary_risk_level": self.preliminary_risk_level,
            "triggered_pattern_names": [p.name for p in self.triggered_patterns],
            "high_level_pattern_names": [p.name for p in self.high_level_triggers],
        }


# ---------------------------------------------------------------------------
# Core mapping function
# ---------------------------------------------------------------------------

def triage_clause(
    clause_text: str,
    patterns: Optional[List[RiskPattern]] = None,
) -> RiskMapperResult:
    """
    Alias for map_clause_risk — triage a single clause through the rule engine.

    Parameters
    ----------
    clause_text:
        Text of the clause to analyse.
    patterns:
        Override the master list (useful for unit-testing subsets).

    Returns
    -------
    RiskMapperResult
    """
    return map_clause_risk(clause_text, patterns)


def map_clause_risk(
    clause_text: str,
    patterns: Optional[List[RiskPattern]] = None,
) -> RiskMapperResult:
    """
    Run all (or supplied) patterns against *clause_text* and return a triage.

    Triage rules
    ─────────────
    GREEN  : 0 pattern matches
    YELLOW : 1–2 matches  AND  no HIGH-level pattern triggered
    RED    : 3+ matches   OR   any single HIGH-level pattern triggered

    Parameters
    ----------
    clause_text:
        Text of the clause to analyse.
    patterns:
        Override the master list (useful for unit-testing subsets).

    Returns
    -------
    RiskMapperResult
    """
    if patterns is None:
        patterns = ALL_PATTERNS

    if not clause_text or not clause_text.strip():
        return RiskMapperResult(
            triage=TriageLevel.GREEN,
            match_count=0,
        )

    triggered: List[RiskPattern] = []
    high_triggers: List[RiskPattern] = []

    for pattern in patterns:
        if pattern.matches(clause_text):
            triggered.append(pattern)
            if pattern.risk_level == RiskLevel.HIGH:
                high_triggers.append(pattern)

    match_count = len(triggered)

    # ── Triage logic ────────────────────────────────────────────────────
    if match_count == 0:
        triage = TriageLevel.GREEN
    elif high_triggers:
        # Any HIGH-level hit → RED immediately, regardless of total count
        triage = TriageLevel.RED
    elif match_count >= 3:
        triage = TriageLevel.RED
    else:
        # 1 or 2 MEDIUM-only matches
        triage = TriageLevel.YELLOW

    result = RiskMapperResult(
        triage=triage,
        match_count=match_count,
        triggered_patterns=triggered,
        high_level_triggers=high_triggers,
    )

    logger.debug(
        "Triage=%s count=%d high=%d patterns=%s",
        triage.value,
        match_count,
        len(high_triggers),
        [p.name for p in triggered],
    )
    return result


# ---------------------------------------------------------------------------
# Batch helper (processes a list of clauses)
# ---------------------------------------------------------------------------

@dataclass
class ClauseTriage:
    index: int
    text: str
    result: RiskMapperResult


def triage_clauses(
    clauses: List[str],
    patterns: Optional[List[RiskPattern]] = None,
) -> List[ClauseTriage]:
    """
    Run risk mapping on a list of clause strings and return ordered results.

    Parameters
    ----------
    clauses:
        Ordered list of clause text strings.
    patterns:
        Override the pattern list.

    Returns
    -------
    List[ClauseTriage] in the same order as *clauses*.
    """
    return [
        ClauseTriage(index=i, text=text, result=map_clause_risk(text, patterns))
        for i, text in enumerate(clauses)
    ]


def partition_by_triage(
    triaged: List[ClauseTriage],
) -> dict[str, List[ClauseTriage]]:
    """
    Split a list of ClauseTriage objects into GREEN / YELLOW / RED buckets.

    Returns
    -------
    dict with keys "GREEN", "YELLOW", "RED".
    """
    buckets: dict[str, List[ClauseTriage]] = {
        TriageLevel.GREEN.value:  [],
        TriageLevel.YELLOW.value: [],
        TriageLevel.RED.value:    [],
    }
    for ct in triaged:
        buckets[ct.result.triage.value].append(ct)
    return buckets